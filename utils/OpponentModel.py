#things that aren't super clear to me get:
#Do I know what domain we are in from the get go? Probably
#So I guess that means I immediately know what issues we are negotiating on right? yup
#How is preference ordering different form the issue weights?

#first let's put in some default values for opponent

# what is a concession ratio? concede = willing to lose
#


from typing import cast

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.Offer import Offer
from geniusweb.actions.PartyId import PartyId
from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.Settings import Settings
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.issuevalue.Bid import Bid
from geniusweb.issuevalue.Domain import Domain
from geniusweb.issuevalue.Value import Value
from geniusweb.issuevalue.ValueSet import ValueSet
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profile.utilityspace.UtilitySpace import UtilitySpace
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)
from geniusweb.progress.ProgressRounds import ProgressRounds
from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel

import numpy as np
class OpponentModel:

#todo gotta do some clean up now! try and merge OpponentModelImproved and this class


    def __init__(self, profile):
        self._issueWeights = None

        self._biddingHistory = []
        self._utilityBiddingHistory = None
        self._concessionRatioToWeight = 1 - np.arange(100)/100
        self._roundNumber = 1
        self._concessionRatioDistributions = []
        self._reservationValue = 0
        self._windows = []
        self._profile = profile
        self._issues = profile.getProfile().getDomain().getIssues()
        self._frequencyModel = FrequencyOpponentModel.create().With(profile.getProfile().getDomain(), newResBid=None)






    def updateBiddingHistory(self, newBid: Bid):
        self._biddingHistory.append(newBid)
        if(len(self._biddingHistory)>1):
            self.updateIssueWeights()

    def getOpponentUtility(self, potentialBid: Bid):
        sum = 0
        issueValues = potentialBid.getIssueValues()
        for counter,issue in enumerate(self._issues):
            sum += self._issueWeights[counter] * self._frequencyModel._getFraction(issue, self._frequencyModel.val(issueValues[issue]))
        return sum

    roundNumber = 0
    def updateIssueWeights(self):
        # first step: we compare 2 consecutive bids, and measure how much each issue decreases in terms of proportion.


        currentBid = self._biddingHistory[len(self._biddingHistory)-1]
        previousBid = self._biddingHistory[len(self._biddingHistory)-2]

        previousBidValues = previousBid.getIssueValues()
        currentBidBidValues = currentBid.getIssueValues()
        concessionRatios = np.empty(len(self._issues))
        estimatedIssueWeights = np.empty(len(self._issues))



        for counter,issue in enumerate(self._issues):
            ratio = self._frequencyModel._getFraction(issue, self._frequencyModel.val(currentBidBidValues[issue]))/self._frequencyModel._getFraction(issue, self._frequencyModel.val(previousBidValues[issue]))
            concessionRatios[counter] = ratio

        self._concessionRatioDistributions.append(concessionRatios)


        for counter, concessionRatio in enumerate(concessionRatios):
            estimatedIssueWeights[counter] = self.mapConcessionRatiosToIssueWeights(concessionRatio)
        estimatedIssueWeights = estimatedIssueWeights/np.sum(estimatedIssueWeights)

        self._issueWeights = self._issueWeights + (estimatedIssueWeights - self._issueWeights) / self._roundNumber
        self._roundNumber += 1
        self._issueWeights = self._issueWeights/np.sum(self._issueWeights)





    def mapConcessionRatiosToIssueWeights(self,concessionRatio):

        #vectorizing the array for convenience and speed
        vectorizedConcessionRatioDistributions = np.array(self._concessionRatioDistributions)

        # calculating in what percentile the concession ratio is
        percentile = int(len(
            vectorizedConcessionRatioDistributions[vectorizedConcessionRatioDistributions < concessionRatio])
                         *100/len(self._concessionRatioDistributions))
        return self._concessionRatioToWeight[percentile]


    def notifyChange(self, info: Inform):
        if isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer):
                bid = cast(Offer, action).getBid()
                #updates bidding history and weights
                self.updateBiddingHistory(bid)
    def estimateReservationValue(self):
        self.updateUtilities()
        self.detectWindows()

        #the convolution reduce some noise
        #todo maybe do some fun stuff with fourier, but gotta see first
        utilityBiddingHistory = np.convolve(self._utilityBiddingHistory,np.ones(5)/5)


        windowStart = 0

        reservationValueEstimates = []

        for windowFinish in self._windows:
            maxLag =  windowStart - windowFinish

            #every possible lag between 2 bids
            for lag in range(maxLag):
                tuples = np.empty(windowFinish - lag - windowStart)

                #storing this in tuples of 2 bids
                for x in range(windowStart,windowFinish - lag):
                    tuples[x-windowStart] = (utilityBiddingHistory[x],utilityBiddingHistory[x+lag])
                for x in range(len(tuples)-2):
                    for y in range(x+1,len(tuples)):
                        (u1_x, u2_x) = tuples[x]
                        (u1_y, u2_y) = tuples[y]
                        reservationValueEstimate = (u1_x * u2_y - u2_x * u1_y)/(u1_x - u2_x + u1_y - u2_y)
                        # only add reservation value if it makes sense (so it's not negative or above the latest utility they offered)
                        if(reservationValueEstimate <= utilityBiddingHistory[-1] and reservationValueEstimate >= 0):
                            reservationValueEstimates.append(reservationValueEstimate)
        reservationValueEstimates = np.array(reservationValueEstimate)
        return np.mean(reservationValueEstimates)

    def detectWindows(self):
        firstDerivative = self._utilityBiddingHistory[0:-2] - self._utilityBiddingHistory[1:-1]
        secondDerivative = np.abs(firstDerivative[0:-2] - firstDerivative[1:-1])
        top20Percent = np.percentile(secondDerivative,80)

        windows = np.sort(np.argwhere(secondDerivative>top20Percent))

        previousWindowStart = 0

        #returns only windows that are at least 10 rounds apart
        for x in range(len(windows)):
            if(previousWindowStart + 10 > windows[x]):
                windows[x] = -1
            else:
                previousWindowStart = windows[x]


        return windows[windows != -1]

    def updateUtilities(self):
        utilities = np.empty(len(self._biddingHistory))
        for x,bid in enumerate(self._biddingHistory):
            utilities[x] = self._frequencyModel.getUtility(bid)
        self._utilityBiddingHistory = utilities









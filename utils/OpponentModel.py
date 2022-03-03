#things that aren't super clear to me get:
#Do I know what domain we are in from the get go? Probably
#So I guess that means I immediately know what issues we are negotiating on right? yup
#How is preference ordering different form the issue weights?

#first let's put in some default values for opponent

# what is a concession ratio? concede = willing to lose
#


import logging
from random import randint
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


    def __init__(self):
        self._issueWeights = None

        self._biddingHistory = []
        self._issues = None
        self._concessionRatioToWeight = 1 - np.arange(100)/100
        self._roundNumber = 1
        self._concessionRatioDistributions = None


        self._profile = None

        self._frequencyModel = None
    def setIssueWeights(self, issuesTotal):
        self._issueWeights = np.ones(issuesTotal)

    def setConcessionRatioDistributions(self, issuesTotal):
        self._concessionRatioDistributions = np.array([])


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
            difference = self._frequencyModel._getFraction(issue, self._frequencyModel.val(previousBidValues[issue]))  - currentBidBidValues[issue]
            concessionRatios[counter] = difference

        self._concessionRatioDistributions.append(concessionRatios)

        #
        for counter, concessionRatio in enumerate(concessionRatios):
            estimatedIssueWeights[counter] = self.mapConcessionRatiosToIssueWeights(concessionRatio)
        estimatedIssueWeights = estimatedIssueWeights/np.sum(estimatedIssueWeights)

        self._issueWeights = self._issueWeights + (estimatedIssueWeights - self._issueWeights) / self._roundNumber
        self._roundNumber += 1
        self._issueWeights = self._issueWeights/np.sum(self._issueWeights)





    def mapConcessionRatiosToIssueWeights(self,concessionRatio):
        percentile = int(len(self._concessionRatioDistributions[self._concessionRatioDistributions<concessionRatio])*100/len(self._concessionRatioDistributions))
        return self._concessionRatioToWeight[percentile]


    def notifyChange(self, info: Inform):
        """This is the entry point of all interaction with your agent after is has been initialised.

        Args:
            info (Inform): Contains either a request for action or information.
        """
        # a Settings message is the first message that will be send to your
        # agent containing all the information about the negotiation session.
        if isinstance(info, Settings):
            self._settings: Settings = cast(Settings, info)
            self._me = self._settings.getID()

            self._issues = self._settings.getProfile().getDomain().getIssues()

            # progress towards the deadline has to be tracked manually through the use of the Progress object
            self._progress: ProgressRounds = self._settings.getProgress()

            # the profile contains the preferences of the agent over the domain
            self._profile = ProfileConnectionFactory.create(
                info.getProfile().getURI(), self.getReporter()
            )
            self._frequencyModel = FrequencyOpponentModel.create().With(self._profile.getProfile().getDomain(), newResBid=None)

        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer):
                bid = cast(Offer, action).getBid()
                #updates bidding history and weights
                self.updateBiddingHistory(bid)











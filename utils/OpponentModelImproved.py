import numpy as np
import logging
import math
import sys
from decimal import Decimal
from typing import cast, List

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.Offer import Offer
from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.Settings import Settings
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.issuevalue.Bid import Bid
from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)
from geniusweb.progress.Progress import Progress

from utils.OpponentModel import OpponentModel


class OpponentModelImproved:
    def __init__(self):
        self._reservationValue = 0;
        #self._biddingHistory = np.array([])
        self._utilityBiddingHistory = np.array([])
        self._opponentModel = OpponentModel()
        #self._utilityBiddingHistory = np.array([])

        self._predictedReservationValues = np.array([])
        #round number where new window happens
        # purpose is to change when strategy seems to change
        self._windows = []

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
        utilities = np.empty(len(OpponentModel._biddingHistory))
        for x,bid in enumerate(OpponentModel._biddingHistory):
            utilities[x] = self._frequencyModel.getUtility(bid)
        self._utilityBiddingHistory = utilities;



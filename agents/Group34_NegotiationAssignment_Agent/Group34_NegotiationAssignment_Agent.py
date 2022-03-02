import decimal
import logging
import sys
from random import randint
from typing import cast
from typing import Callable


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


class Ye(DefaultParty):
    """
    Template agent that offers random bids until a bid with sufficient utility is offered.
    """

    def __init__(self):
        super().__init__()
        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile = None
        self._last_received_bid: Bid = None
        self._best_util: int = -sys.maxsize - 1

        self._e = 2
        self._to_factor = 1

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

            # progress towards the deadline has to be tracked manually through the use of the Progress object
            self._progress: ProgressRounds = self._settings.getProgress()

            # the profile contains the preferences of the agent over the domain
            self._profile = ProfileConnectionFactory.create(
                info.getProfile().getURI(), self.getReporter()
            )
        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer):
                self._last_received_bid = cast(Offer, action).getBid()

                profile = self._profile.getProfile()

                bid_util = profile.getUtility(cast(Offer, action).getBid())

                if bid_util > self._best_util:
                    self._best_util = bid_util

        # YourTurn notifies you that it is your turn to act
        elif isinstance(info, YourTurn):
            # execute a turn
            self._myTurn()

            # log that we advanced a turn
            self._progress = self._progress.advance()

        # Finished will be send if the negotiation has ended (through agreement or deadline)
        elif isinstance(info, Finished):
            # terminate the agent MUST BE CALLED
            self.terminate()
        else:
            self.getReporter().log(
                logging.WARNING, "Ignoring unknown info " + str(info)
            )

    # lets the geniusweb system know what settings this agent can handle
    # leave it as it is for this course
    def getCapabilities(self) -> Capabilities:
        return Capabilities(
            set(["SAOP"]),
            set(["geniusweb.profile.utilityspace.LinearAdditive"]),
        )

    # terminates the agent and its connections
    # leave it as it is for this course
    def terminate(self):
        self.getReporter().log(logging.INFO, "party is terminating:")
        super().terminate()
        if self._profile is not None:
            self._profile.close()
            self._profile = None

    #######################################################################################
    ########## THE METHODS BELOW THIS COMMENT ARE OF MAIN INTEREST TO THE COURSE ##########
    #######################################################################################

    # give a description of your agent
    def getDescription(self) -> str:
        return "Template agent for Collaborative AI course"

    def big_f(self) -> float:
        # δ ∗ (1 − t^ (1/e) )
        return self._to_factor * (1 - self._progress.get(0) ** (1 / self._e))

    def fitness(self, bid: Bid) -> float:
        # F (t) ∗ u(ω) + (1 − F (t)) ∗ fn(ω)
        # ω - our bid

        F = self.big_f()

        profile = self._profile.getProfile()

        return F * float(profile.getUtility(bid)) + (1 - F) * self.f5(bid) # for now f1

    def f5(self, bid: Bid) -> float:
        # opponent utility
        return 0.5 # getOpponentUtility(bid)

    def f1(self, bid: Bid) -> float:
        # f1(ω) = 1 − |uˆo(ω) − uˆo (xlast)|
        return 1 - abs(self.f5(bid) - self.f5(self._last_received_bid))

    def f2(self, bid: Bid) -> float:
        # f2(ω) = min(1 + uˆo (ω) − uˆo (xlast), 1)
        return min(1 + self.f5(bid) - self.f5(self._last_received_bid), 1)

    def f3(self, bid: Bid) -> float:
        # f3(ω) = 1 − |uˆo (ω) − uˆo (x+)|
        return 1 - abs(self.f5(bid) - self._best_util)

    def f4(self, bid: Bid) -> float:
        # f4(ω) = min(1 + uˆo (ω) − uˆo (x+), 1)
        return min(1 + self.f5(bid) - self._best_util, 1)

    # execute a turn
    def _myTurn(self):
        # check if the last received offer if the opponent is good enough
        if self._isGood(self._last_received_bid):
            # if so, accept the offer
            action = Accept(self._me, self._last_received_bid)
        else:
            # if not, find a bid to propose as counter offer
            bid = self._findBid()
            action = Offer(self._me, bid)

        # send the action
        self.getConnection().send(action)

    # method that checks if we would agree with an offer
    def _isGood(self, bid: Bid) -> bool:
        if bid is None:
            return False
        profile = self._profile.getProfile()

        progress = self._progress.get(0)

        # very basic approach that accepts if the offer is valued above 0.6 and
        # 80% of the rounds towards the deadline have passed
        # return profile.getUtility(bid) > 0.6 and progress > 0.8

        return False

    def _findBid(self) -> Bid:
        # compose a list of all possible bids
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)

        # profile = self._profile.getProfile().getReservationBid()

        best_util = -sys.maxsize - 1
        best_bid = None

        for bid in all_bids:
            bid_util = self.fitness(bid)

            if bid_util > best_util:
                best_bid = bid
                best_util = bid_util



        return best_bid

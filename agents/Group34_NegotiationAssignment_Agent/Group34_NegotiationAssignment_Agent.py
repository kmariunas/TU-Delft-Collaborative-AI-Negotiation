import json
import logging
import math
import sys
from decimal import Decimal
from os import path
from typing import cast, List, Dict

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.Offer import Offer
from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.bidspace.Interval import Interval
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.Settings import Settings
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.issuevalue.Bid import Bid
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)
from geniusweb.progress.Progress import Progress

from agents.Group34_NegotiationAssignment_Agent.DistributionBasedFrequencyOpponentModel import \
    DistributionBasedFrequencyOpponentModel


class Ye(DefaultParty):
    """
    Template agent that offers random bids until a bid with sufficient utility is offered.
    """

    def __init__(self):
        super().__init__()
        self._progress = None
        self._me = None
        self._settings = None
        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile = None
        self._last_received_bid = None
        self._best_util: int = -sys.maxsize - 1
        self._received_bids: List[Bid] = list()
        self._opponent_model: DistributionBasedFrequencyOpponentModel = None

        basepath = path.dirname(__file__)

        self._file_name = path.abspath(path.join(basepath, "..", "..", "results/received-bids-utilities.json"))
        self._received_bids_utilities: List[float] = []

        self.opponent_file_name = path.abspath(path.join(basepath, "..", "..", "results/opponent-weights.json"))
        self.opponent_weights: List[Dict[str, float]] = []

        finetune_params = json.loads(open(path.abspath(path.join(basepath, "..", "..", "results/parameters_read.json")),
                                          encoding='utf-8').read())

        print(f"Iteration {finetune_params[0]} of Set{math.floor(finetune_params[0] / 96)}")

        params = finetune_params[1][math.floor(finetune_params[0] / 96)]

        self._e = params["e"]
        self._to_factor = params["to_factor"]
        self.our_last_sent_bid = None
        self._window_size = params["window_size"]
        self._max_concession = params["max_concession"]
        self.fn = None

        if params["fit"] == 1:
            self.fittness_function = self.fitness
        elif params["fit"] == 2:
            self.fittness_function = self.fitness2

        if params["fn"] == 1:
            self.fn = self.f1
        elif params["fn"] == 2:
            self.fn = self.f2
        elif params["fn"] == 3:
            self.fn = self.f3
        elif params["fn"] == 4:
            self.fn = self.f4
        elif params["fn"] == 5:
            self.fn = self.f5

        self.alpha = params["alpha"]
        self.beta = params["beta"]
        self.time = params["time"]
        self.a_const = params["a_const"]

        if params["ac"] == 1:
            self.ac = self.ac_max
        elif params["ac"] == 2:
            self.ac = self.ac_avg

        finetune_params[0] = finetune_params[0] + 1

        with open(path.abspath(path.join(basepath, "..", "..", "results/parameters_read.json")), "w") as f:
            f.write(json.dumps(finetune_params, indent=2))

    def notifyChange(self, info: Inform):
        """This is the entry point of all interaction with your agent after is has been initialised.

        Args:
            info (Inform): Contains either a request for action or information.
        """

        # a Settings message is the first message that will be sent to your
        # agent containing all the information about the negotiation session.
        if isinstance(info, Settings):

            self._settings: Settings = cast(Settings, info)
            self._me = self._settings.getID()

            # progress towards the deadline has to be tracked manually through the use of the Progress object
            self._progress: Progress = self._settings.getProgress()

            # the profile contains the preferences of the agent over the domain
            self._profile = ProfileConnectionFactory.create(
                info.getProfile().getURI(), self.getReporter()
            )

            self._opponent_model = DistributionBasedFrequencyOpponentModel \
                .create(self._window_size, alpha=1.3 / len(self._profile.getProfile().getDomain().getIssues())) \
                .With(self._profile.getProfile().getDomain(), newResBid=None)
            # self._opponent_model.dom

            self._bids_space = BidsWithUtility.create(self._profile.getProfile(), 6)

        # ActionDone is an action sent by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = info.getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer) and action.getActor() is not self._me:
                self._last_received_bid: Bid = action.getBid()

                profile = self._profile.getProfile()
                bid_util = profile.getUtility(self._last_received_bid)
                if bid_util > self._best_util:
                    self._best_util = float(bid_util)

                # add bid to the received bids list
                self._received_bids.append(self._last_received_bid)

                # add bid to opponent model
                self._opponent_model = self._opponent_model.WithAction(action, self._progress)

        # YourTurn notifies you that it is your turn to act
        elif isinstance(info, YourTurn):
            # execute a turn
            self._myTurn()

            # log that we advanced a turn
            self._progress = self._progress.advance()

        # Finished will be sent if the negotiation has ended (through agreement or deadline)
        elif isinstance(info, Finished):
            # terminate the agent MUST BE CALLED
            # print(self._opponent_model.getIssueWeights())

            # TODO: write files if you wanna do plots
            # self.write_weights()
            # self.write_utilities()

            self.terminate()
        else:
            self.getReporter().log(
                logging.WARNING, "Ignoring unknown info " + str(info)
            )

    # lets the geniusweb system know what settings this agent can handle
    # leave it as it is for this course
    def getCapabilities(self) -> Capabilities:
        return Capabilities(
            {"SAOP"},
            {"geniusweb.profile.utilityspace.LinearAdditive"},
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

        return F * float(profile.getUtility(bid)) + (1 - F) * self.fn(bid)

    def fitness2(self, bid: Bid) -> float:
        # u(w) + t^(1/e) * u'(w)
        progress = self._progress.get(0)

        profile = self._profile.getProfile()
        bid_util = profile.getUtility(bid)
        opponent_util = self.fn(bid)
        return float(profile.getUtility(bid)) + (progress ** (1 / self._e)) * self.fn(bid)

    def f5(self, bid: Bid) -> float:
        # opponent utility
        return float(self._opponent_model.getUtility(bid))

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
        # find a bid to propose as counter offer
        bid = self._findBid()

        # check if the last received offer if the opponent is good enough
        if self._isGood(self._last_received_bid, bid):
            # if so, accept the offer
            action = Accept(self._me, self._last_received_bid)
        else:
            # otherwise, offer the new bid
            action = Offer(self._me, bid)

        self.our_last_sent_bid = bid
        # send the action
        self.getConnection().send(action)

    def _isGood(self, opponent_bid: Bid, agent_bid: Bid) -> bool:
        """
        Method that checks if we would agree with an offer

        :param opponent_bid
        :param agent_bid: the bid that the agent is considering to offer
        :return True iff agent should accept opponent's bid.
        """
        if opponent_bid is None:
            return False

        # print(2*int(self._progress.get(0) * 200), " - ", self._opponent_model.getUtility(opponent_bid))

        reservation_bid = self._profile.getProfile().getReservationBid()
        if reservation_bid is not None:
            reservation_value = self._profile.getProfile().getUtility()
        else:
            reservation_value = 0
        # if the received bid has utility greater than our reservation value
        if self._profile.getProfile().getUtility(opponent_bid) > reservation_value:
            # check acceptance conditions
            # if any of them return True (bid is good) => return true
            return self.ac_const(opponent_bid, alpha=self.a_const) or \
                   self.ac_next(opponent_bid, agent_bid, alpha=self.alpha, beta=self.beta) or \
                   self.ac(opponent_bid, time=self.time)
        else:
            return False

    def ac_const(self, opponent_bid: Bid, alpha: Decimal = Decimal(0.88)) -> bool:
        """
        Acceptance condition, constant utility value.

        Method returns true if the passed bid has utility greater than alpha
        :param opponent_bid
        :param alpha: the utility for which we should accept the bid.
        """
        bid_utility = self._profile.getProfile().getUtility(opponent_bid)

        return bid_utility >= alpha

    def ac_next(self, opponent_bid: Bid, agent_bid: Bid, alpha: float = 1.015, beta: float = 0.017) -> bool:
        """
        Acceptance condition, compares opponent's bid with the bid we are about to propose.

        Method returns true if opponent's bid has greater utility than the provided (potential) bid
        :param opponent_bid
        :param agent_bid: the bid that the agent would offer next.
        """
        profile = self._profile.getProfile()
        return float(profile.getUtility(opponent_bid)) >= alpha * float(profile.getUtility(agent_bid)) + beta

    def ac_avg(self, opponent_bid: Bid, time: float = 0.925) -> bool:
        """
        Acceptance condition, compares opponent's bid with the average of previously offered bids.

        Method returns true if, given that the current negotiation round happens after the time 'time',
        the opponent's bid has greater utility than the average utility of (some of) the past offered bids.
        As the negotiation round approaches it's end, the method considers a smaller set of previous bid.
        ie: progress = 0.98 => calculate average of last 4 offered bids
            progress = 0.99 => calculate average of last 2 offered bids
            here, I assume the negotiation has duration of 200 rounds
        :param opponent_bid
        :param time: TODO
        """
        progress = self._progress.get(0)
        if progress >= time:
            # get average of utility of received bids in the time interval [p - r; p]
            # where p = progress, here it is a float, ie: 0.99
            # r = remaining time
            remaining_time = 1 - progress
            max_rounds = self._progress.getDuration()
            interval_start = math.floor((progress - remaining_time) * max_rounds)

            utility_sum = 0
            num_bids = 0
            for bid in self._received_bids[interval_start:]:
                utility_sum += self._profile.getProfile().getUtility(bid)
                num_bids += 1

            avg = utility_sum / num_bids

            return self._profile.getProfile().getUtility(opponent_bid) >= avg

        return False

    def ac_max(self, opponent_bid: Bid, time: float = 0.92) -> bool:
        """
        Acceptance condition, compares opponent's bid with the best previously offered bid.

        Method returns true if, given that the current negotiation round happens after the time 'time',
        the opponent's bid has greater utility than the max utility of (some of) the past offered bids.
        As the negotiation round approaches it's end, the method considers a smaller set of previous bid.
        ie: progress = 0.98 => calculate average of last 4 offered bids
            progress = 0.99 => calculate average of last 2 offered bids
            here, I assume the negotiation has duration of 200 rounds
        :param opponent_bid
        :param time: TODO
        """
        progress = self._progress.get(0)
        if progress >= time:
            # get average of utility of received bids in the time interval [p - r; p]
            # where p = progress, here it is a float, ie: 0.99
            # r = remaining time
            remaining_time = 1 - progress
            max_rounds = self._progress.getDuration()
            interval_start = math.floor((progress - remaining_time) * max_rounds)

            max_util = Decimal(0)
            for bid in self._received_bids[interval_start:]:
                bid_utility = self._profile.getProfile().getUtility(bid)
                max_util = max(max_util, bid_utility)

            # TODO: check that max_util > 0 ??

            return self._profile.getProfile().getUtility(opponent_bid) > max_util

        return False

    def _findBid(self) -> Bid:
        # TODO: figure out if opponent strategy and react to it
        if self._last_received_bid is not None:
            self._received_bids_utilities.append(float(self._opponent_model.getUtility(self._last_received_bid)))
            self.opponent_weights.append(self._opponent_model.getIssueWeights())

        if self.our_last_sent_bid is None:
            max_util = 1.0
        else:
            max_util = float(self._profile.getProfile().getUtility(self.our_last_sent_bid))

        # compose a list of all possible bids
        all_bids = self._bids_space.getBids(
            Interval(Decimal(max_util - self._max_concession), Decimal(max_util + 0.01)))

        best_util = -sys.maxsize - 1
        best_bid = None

        for bid in all_bids:
            bid_util = self.fittness_function(bid)

            if bid_util > best_util:
                best_bid = bid
                best_util = bid_util

        return best_bid

    def write_utilities(self):
        json_string = json.dumps(self._received_bids_utilities)
        with open(self._file_name, 'w') as outfile:
            json.dump(json_string, outfile)

    def write_weights(self):
        # weights = {"weights": self.opponent_weights}
        json_string = json.dumps(self.opponent_weights)
        with open(self.opponent_file_name, 'w') as outfile:
            json.dump(json_string, outfile)
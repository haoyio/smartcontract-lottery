import pytest
import time
from brownie import network
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
)


# test on real testnet; you still want all the code tested,
# not just what we're doing here
def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # can randomly add +1000 to entrance fee for numerical issues
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})

    n_minutes_waited = 0
    while lottery.lottery_state() == 2 and n_minutes_waited < 10:  # calculating winner
        time.sleep(60)  # sleep for 1 min
        print(f"lottery_state = {lottery.lottery_state()}")
        n_minutes_waited += 1

    if lottery.lottery_state() == 2:  # calculating winner
        print(f"Timed out waiting for fulfillRandomness...")
        pytest.skip()
    else:
        assert lottery.recentWinner() == account
        assert lottery.balance() == 0

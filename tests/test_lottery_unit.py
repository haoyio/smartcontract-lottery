import pytest
from web3 import Web3

from brownie import exceptions, network
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    get_account,
    get_contract,
)


def test_get_entrance_fee():
    # old
    # 50/4000 = 0.0125 ETH as of Dec 4, 2021
    # account = accounts[0]
    # lottery = Lottery.deploy(
    #     config["networks"][network.show_active()]["eth_usd_price_feed"],
    #     {"from": account},
    # )
    # assert lottery.getEntranceFee() > Web3.toWei(0.005, "ether")
    # assert lottery.getEntranceFee() < Web3.toWei(0.020, "ether")
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    # 2k eth/usd, usdEntryFee is 50, 2k/1=50/x => x = 0.025
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntranceFee()
    assert entrance_fee == expected_entrance_fee


def test_cant_enter_unless_starting():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # index into contract array w/ parentheses, not square brackets
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # note that lottery_state is a .method(), not just an .instance_variable
    assert lottery.lottery_state() == 2  # CALCULATING_WINNER


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    transaction = lottery.endLottery({"from": account})
    # very useful to use events to test (among many other things)
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 778
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id,
        STATIC_RNG,
        lottery.address,
        {"from": account},  # always need from account for state changes
    )
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    # note STATIC_RNG = 778 % 3 == 1, so it's the 2nd account (index=1) that wins
    assert lottery.recentWinner() == get_account(index=1)
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery

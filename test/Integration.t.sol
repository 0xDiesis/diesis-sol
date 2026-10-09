// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {DiesisAddresses} from "diesis-sol/DiesisAddresses.sol";
import {DiesisChains} from "diesis-sol/DiesisChains.sol";
import {IDiesisStaking} from "diesis-sol/interfaces/IDiesisStaking.sol";
import {IWrappedDS} from "diesis-sol/interfaces/IWrappedDS.sol";
import {IDiesisMarkets} from "diesis-sol/interfaces/IDiesisMarkets.sol";

interface Vm {
    function etch(address target, bytes calldata code) external;
    function deal(address account, uint256 balance) external;
}

contract StakingMock {
    function stake(uint256 validatorId) external payable returns (uint256) {
        require(validatorId == 7 && msg.value == 1 ether, "wrong stake calldata/value");
        return 42;
    }

    function unclaimedRewards(uint256 tokenId) external pure returns (uint256) {
        require(tokenId == 42, "wrong token");
        return 3 ether;
    }
}

contract WrappedMock {
    function balanceOf(address account) external pure returns (uint256) {
        require(account != address(0), "zero account");
        return 5 ether;
    }

    function deposit() external payable {
        require(msg.value == 2 ether, "wrong deposit value");
    }
}

contract MarketsMock {
    function getMarket(bytes32 marketId) external pure returns (IDiesisMarkets.PackedMarket memory) {
        return IDiesisMarkets.PackedMarket(marketId, bytes32(uint256(2)), 100);
    }
}

/// @dev Local mocks test the generated call ABI. These are not live-node tests.
contract IntegrationTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    function setUp() public {
        vm.etch(DiesisAddresses.DIESIS_STAKING, address(new StakingMock()).code);
        vm.etch(DiesisAddresses.WRAPPED_DS, address(new WrappedMock()).code);
        vm.etch(DiesisAddresses.DIESIS_MARKETS, address(new MarketsMock()).code);
        vm.deal(address(this), 10 ether);
    }

    function testPayableStakeAndRewardRead() public {
        IDiesisStaking staking = IDiesisStaking(DiesisAddresses.DIESIS_STAKING);
        uint256 tokenId = staking.stake{value: 1 ether}(7);
        require(tokenId == 42, "token id");
        require(staking.unclaimedRewards(tokenId) == 3 ether, "rewards");
    }

    function testWrappedDsBalanceAndDeposit() public {
        IWrappedDS wrapped = IWrappedDS(payable(DiesisAddresses.WRAPPED_DS));
        require(wrapped.balanceOf(address(this)) == 5 ether, "balance");
        wrapped.deposit{value: 2 ether}();
        require(DiesisAddresses.WRAPPED_DS.balance == 2 ether, "deposit");
    }

    function testDecodeMarketTuple() public view {
        IDiesisMarkets.PackedMarket memory market = IDiesisMarkets(DiesisAddresses.DIESIS_MARKETS).getMarket(bytes32(uint256(1)));
        require(market.slot0 == bytes32(uint256(1)) && market.slot1 == bytes32(uint256(2)) && market.maxOpenInterest == 100, "market tuple");
    }

    function testCanonicalIdsAndSelectors() public pure {
        require(DiesisChains.MAINNET == 1980 && DiesisChains.TESTNET == 19803, "chain ids");
        require(IDiesisStaking.stake.selector == bytes4(keccak256("stake(uint256)")), "stake selector");
        require(IWrappedDS.balanceOf.selector == bytes4(keccak256("balanceOf(address)")), "balance selector");
    }
}

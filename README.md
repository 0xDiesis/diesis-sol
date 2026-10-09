# diesis-sol

Solidity interfaces and address constants for integrating smart contracts with
Diesis. Install this SDK on its own. You do not need the node, system contract
implementations, or their dependencies to compile your application.

The SDK contains 29 public contract interfaces generated with
[abi-typegen](https://github.com/doublesharp/abi-typegen) **0.8.0**, including
their tuple structs, events, errors, overloads, and payable/view declarations.
`DiesisAddresses` contains every address in the same `canonical.json` used by
[diesis-js](https://github.com/0xDiesis/diesis-js). `DiesisChains.MAINNET` is
`1980`; `DiesisChains.TESTNET` is `19803`.

## Install with Foundry

```sh
forge install 0xDiesis/diesis-sol@<commit>
```

Use an immutable commit from this repository. The repository is private,
like the other Diesis SDK repositories, so Git access must be authenticated.
Add this line to your project's `remappings.txt`:

```text
diesis-sol/=lib/diesis-sol/src/
```

The generated interfaces require Solidity 0.8.4 or newer for custom errors.
The SDK's tests use Solidity 0.8.35. No runtime or Solidity library dependency
is required. Hardhat users can place a checkout in their project and import
the `.sol` files from its `src` directory.

## Read system contracts

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {DiesisAddresses} from "diesis-sol/DiesisAddresses.sol";
import {IDiesisStaking} from "diesis-sol/interfaces/IDiesisStaking.sol";
import {IWrappedDS} from "diesis-sol/interfaces/IWrappedDS.sol";
import {IDiesisMarkets} from "diesis-sol/interfaces/IDiesisMarkets.sol";

contract DiesisReader {
    function rewards(uint256 tokenId) external view returns (uint256) {
        return IDiesisStaking(DiesisAddresses.DIESIS_STAKING).unclaimedRewards(tokenId);
    }

    function wrappedBalance(address owner) external view returns (uint256) {
        return IWrappedDS(payable(DiesisAddresses.WRAPPED_DS)).balanceOf(owner);
    }

    function market(bytes32 marketId) external view returns (IDiesisMarkets.PackedMarket memory) {
        return IDiesisMarkets(DiesisAddresses.DIESIS_MARKETS).getMarket(marketId);
    }
}
```

Call payable methods through the same interfaces, for example
`staking.stake{value: amount}(validatorId)`. Calls originate from your contract,
so apply the target contract's ownership and authorization rules to that caller.
Use `IValidatorShare` with a validator's deployed share address. It has no fixed
address in `DiesisAddresses`.

## Interfaces

| Area | Interfaces |
|---|---|
| Trading | `IDiesisMarkets`, `IDiesisSpotBook`, `IDiesisPerpsBook`, `IDiesisMargin`, `IDiesisSettlement`, `IDiesisSettlementRouter`, `IDiesisConductors`, `IDiesisErc20Factory`, `IDiesisPerpDeploy`, `IDiesisOperatorBond` |
| Staking and assets | `IDiesisStaking`, `IDiesisPosition`, `IValidatorShare`, `ILiquidStakedDS`, `IWrappedDS` |
| Sponsorship and system services | `IDiesisPatron`, `IDiesisConfig`, `IDiesisBundleEscrow`, `IDiesisCoreVault`, `IDiesisIssuanceAuction`, `IDiesisBuybackBurn` |
| Privacy | `IDiesisShieldedPool`, `IDiesisPrivacyPools` |
| Names | `IDiesisNameRegistry`, `IDiesisBaseRegistrar`, `IDiesisPublicResolver`, `IDiesisReverseRegistrar`, `IDiesisNameVerifier`, `IDiesisNamePolicy` |

Structs are scoped to their generated interface, such as
`IDiesisMarkets.PackedMarket`. Events and custom errors are available through
the same interface. Import names and filenames retain an existing `I` prefix;
implementation ABIs receive one, so `DiesisStaking` generates `IDiesisStaking.sol`.

## Regenerate from source

Only SDK maintainers need the contracts checkout. In the full workspace the
default is `../../diesis-core/diesis/contracts`. For a standalone SDK checkout,
point `DIESIS_CONTRACTS_DIR` to the contracts directory of a source checkout.
Build that source with its repository's compiler wrapper before regeneration:

```sh
cd "$DIESIS_CONTRACTS_DIR"
./scripts/forge.sh build src --skip test --skip script
```

From this SDK's root, with exact abi-typegen 0.8.0 on PATH:

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
```

`ABI_TYPEGEN` selects a generator executable. `--artifacts` selects a custom
source build output directory. The generator reads those build artifacts
directly, writes only Solidity interfaces and constants, and never copies JSON
ABI files into this repository. Missing or ambiguous contract artifacts and
other generator versions fail before it changes SDK files. `--check` reports
missing, changed, or removed interfaces without writing SDK files.

Canonical constants default to `../diesis-js/canonical.json` in the workspace
and the SDK's `canonical.json` in a standalone checkout. Use `--canonical` or
`DIESIS_CANONICAL_FILE` to specify a canonical source explicitly.

## Develop

```sh
python3 -m unittest discover -s tests -v
forge test
python3 scripts/generate.py --check
python3 scripts/check_abi.py
```

`check_abi.py` compares every compiled interface against the source build,
including nested tuples, return types, mutability, indexed events, and custom
errors. Pass `--artifacts` and `--out` for custom source/SDK build directories.
The Foundry tests use local mocks to verify payable calls and struct decoding.
They do not require a node and do not validate live deployments.

## License

MIT

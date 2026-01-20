# Shadowflake

<p align="center">
    <img width="337.5" height="225" src="https://raw.githubusercontent.com/ItsThatOneJack-Dev/shadowflake/main/resources/shadowflake-450x300.png" alt="Shadowflake">
</p>

<p align="center"><strong>Shadowflake</strong> <em>&mdash; A high-volume-safe, order-preserving identifier.</em></p>

---

<img alt="Python Version from PEP 621 TOML" src="https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FItsThatOneJack-Dev%2Fshadowflake%2Frefs%2Fheads%2Fmain%2Fpyproject.toml&style=for-the-badge">
<img alt="PyPI - Implementation" src="https://img.shields.io/pypi/implementation/shadowflake?style=for-the-badge">
<img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dd/shadowflake?style=for-the-badge">

<img alt="PyPI - License" src="https://img.shields.io/pypi/l/shadowflake?pypiBaseUrl=https%3A%2F%2Ftest.pypi.org&style=for-the-badge">

---

Say hello to Shadowflake, the first of the UXID (Universal Extended Identity Descriptor) family!

## What is a UXID?

UXIDs are a new system of identifiers, they are similar to UUIDs but allow extra descriptive information.

Shadowflake does this by behaving primarily as a universally unique, sortable identifier, but allowing you to optionally provide extra descriptive data.

## What are Shadowflake's features?

Shadowflake acts as a universally unique identifier, which means it

- has a very large amount of possible values (2<sup>98</sup>, to be exact),
- and is safe to use in decentralised systems.

But, Shadowflake has benefits over normal universally unique identifiers, too! Shadowflake is:

- lexicographically sortable,
- safe to expose publicly (it reveals near zero security-damaging information),
- and is chronologically sortable (up to 24 hours into the past).

## How are Shadowflakes structured?

Shadowflakes consist of two main segments, the "core" and the "tail".

All fields of Shadowflakes are encoded with Crockford Base32.

The overall format of a Shadowflake is `[SEQUENCE][MILLISECOND][ENTROPY][CORE CHECK SYMBOL]$[SYSTEM].[NODE].[ID]`. Everything after the core check symbol is optional, but may be either all present or not present at all. Despite the separators in the tail, the fields are fixed length and may not be any smaller or longer than is standardised. The core check symbol is computed according to the algorithm specified as part of Crockford Base32.

For the exact details of each part of the Shadowflake, see below:

### The core

| Field       | Bits | Range / Size                   | Description                                                                          |
| ----------- | ---- | ------------------------------ | ------------------------------------------------------------------------------------ |
| Sequence    | 17   | 0–86,399                       | Rolling counter representing seconds since the anchor time, wrapping every 24 hours. |
| Millisecond | 10   | 0–999                          | Sub-second counter incremented every millisecond.                                    |
| Entropy     | 98   | 2<sup>98</sup> possible values | Cryptographically secure random data used to prevent collisions.                     |

### The tail

| Field  | Type    | Bits | Base32 Chars | Description                                                                               |
| ------ | ------- | ---- | ------------ | ----------------------------------------------------------------------------------------- |
| System | ASCII   | 80   | 16           | Logical system or protocol name. ASCII text encoded as bytes. (Max 10 characters)         |
| Node   | ASCII   | 80   | 16           | Subsystem, node, or instance identifier. ASCII text encoded as bytes. (Max 10 characters) |
| ID     | Integer | 30   | 6            | Application-specific numeric identifier. Encoded as an unsigned integer.                  |

## How do I install Shadowflake?

Shadowflake provides two methods of use, as a library in Python code, and as a standalone program. The standalone program is usable interactively, or as a simple CLI tool. If you want a nice, formatted interactive experience, install Shadowflake with the `fancy` extra.

The standalone program is usable without `[fancy]`, it will just be a bit more ugly.
If you want more info on the standalone program, run `shadowflake --help`.

### With pip

```bash
pip install shadowflake
```

### With uv

```bash
uv add shadowflake
```

or

```bash
uv pip install shadowflake
```

## Usage

### As a library

```python
from shadowflake import Shadowflake

# Generate a simple Shadowflake
uuid = Shadowflake.generate()
print(uuid)  # e.g., "01234ABCDEFGHJKMNPQRSTV5"

# Generate with metadata
uuid = Shadowflake.generate(
    system="AUTH",
    node="API-01",
    id=12345
)
print(uuid)  # e.g., "01234ABCDEFGHJKMNPQRSTV5$..."

# Decode a Shadowflake
result = Shadowflake.decode(uuid)
print(result)
```

### As a CLI tool

```bash
shadowflake generate
# ═══════════════════════════════════════════════════════════
#               Generated Shadowflake
# ═══════════════════════════════════════════════════════════
# 01G2XKMNPQRSTVWXYZ34567890AB
# ═══════════════════════════════════════════════════════════

shadowflake decode 01G2XKMNPQRSTVWXYZ34567890AB
# ═══════════════════════════════════════════════════════════
#               Decoded Shadowflake
# ═══════════════════════════════════════════════════════════
# sequence: 45123
# millisecond: 456
# entropy: 123456789012345678901234567890
# system: None
# node: None
# id: None
# valid: True
# ═══════════════════════════════════════════════════════════
```

## License

Copyright (C) 2026 ItsThatOneJack

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

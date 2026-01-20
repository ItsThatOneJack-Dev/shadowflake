# Shadowflake

A Python implementation of Universal Extended Identity (UXID) format.

---

## Features

- Globally unique identifiers with optional descriptive metadata
- Lexicographically sortable within a 24-hour rolling window
- High-entropy to prevent collisions
- Crockford Base32 encoding for readability

## Installation

Shadowflake provides a standard install in addition to the extra `interactive`.
If you wish to be able to use the `shadowflake` command in your terminal, you can install `shadowflake[interactive]`, and the dependencies will be taken care of automatically.

If you wish to install Shadowflake normally, simply install like this:

```bash
pip install shadowflake
```

or with UV:

```bash
uv add shadowflake
```

## Usage

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

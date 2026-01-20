import secrets
import datetime
import re

class ShadowflakeError(Exception):
    """
    Base exception for Shadowflake UXID operations.

    Raised for general errors during Shadowflake generation or decoding.
    """
    pass

class ShadowflakeChecksumError(ShadowflakeError):
    """
    Raised when a Shadowflake UXID fails checksum validation.

    Indicates that the core section may have been corrupted or tampered with.
    """
    pass

class ShadowflakeLengthError(ShadowflakeError):
    """
    Raised when a Shadowflake core is an invalid length.

    Shadowflake cores must be exactly 26 characters (25 payload + 1 checksum).
    """
    pass

class ShadowflakeMetadataError(ShadowflakeError):
    """
    Raised when Shadowflake metadata is invalid.

    This can occur if:
      - Partial metadata is provided (SYSTEM, NODE, and ID must all be present or all None)
      - SYSTEM or NODE contain invalid characters (must be ASCII A-Z, 0-9, '-' or '_')
      - ID is negative or not an integer
      - Metadata is malformed when decoding
    """
    pass

class Shadowflake:
    """
    Shadowflake UXID generator and decoder.

    Shadowflake is a Python implementation of a Universal Extended Identity (UXID) format.
    UXIDs are globally unique identifiers that may optionally include descriptive metadata.

    Shadowflake UXIDs consist of two sections:
      1. **Core** (required) - 26 characters:
         - 25-character payload: sequence (17 bits), millisecond (10 bits), entropy (98 bits)
         - 1-character checksum
      2. **Tail** (optional) - metadata:
         - SYSTEM: 16 Base32 characters (80 bits)
         - NODE: 16 Base32 characters (80 bits)
         - ID: 6 Base32 characters (30 bits)
         - Format: <CORE>$<SYSTEM>.<NODE>.<ID>
    
    Features:
      - Lexicographically sortable within a 24-hour rolling window
      - High-entropy to prevent collisions
      - Optional metadata for interoperability
      - Crockford Base32 encoding for readability
    """

    @staticmethod
    def generate(
        anchor: datetime.datetime | None = None,
        *,
        system: str | None = None,
        node: str | None = None,
        id: int | None = None,
    ) -> str:
        """
        Generate a new Shadowflake UXID.

        Args:
            anchor (datetime.datetime | None):
                Anchor time for the start of the 24-hour period.
                Defaults to UTC midnight of the current day.
            system (str | None):
                Optional system name (ASCII, max 10 characters) to include in metadata.
            node (str | None):
                Optional node or subsystem name (ASCII, max 10 characters) to include in metadata.
            id (int | None):
                Optional numeric ID (0-1,073,741,823) to include in metadata.

        Returns:
            str: A Shadowflake UXID string. If metadata is included, format is:
                 `<CORE>$<SYSTEM>.<NODE>.<ID>`

        Raises:
            ShadowflakeMetadataError: If partial or invalid metadata is provided.
        """

        meta_used = any(v is not None for v in (system, node, id))
        if meta_used and not all(v is not None for v in (system, node, id)):
            raise ShadowflakeMetadataError("Metadata must be all-or-nothing!")

        if id is not None and (not isinstance(id, int) or id < 0 or id > 1_073_741_823):
            raise ShadowflakeMetadataError("ID must be a non-negative integer less than 1,073,741,823!")

        if system is not None:
            system = system.upper()
            if not re.fullmatch(r"[A-Z0-9\-_]+", system):
                raise ShadowflakeMetadataError(f"Invalid SYSTEM value: {system!r}! (Invalid characters!)")
            if len(system) > 10:
                raise ShadowflakeMetadataError(f"Invalid NODE value: {node!r}! (Too long!)")

        if node is not None:
            node = node.upper()
            if not re.fullmatch(r"[A-Z0-9\-_]+", node):
                raise ShadowflakeMetadataError(f"Invalid NODE value: {node!r}! (Invalid characters!)")
            if len(node) > 10:
                raise ShadowflakeMetadataError(f"Invalid NODE value: {node!r}! (Too long!)")

        now = datetime.datetime.now(datetime.timezone.utc)
        if anchor is None:
            anchor = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            anchor = anchor.replace(microsecond=0)

        delta = now - anchor
        total_ms = int(delta.total_seconds() * 1000)

        millisecond = total_ms % 1000
        sequence = (total_ms // 1000) % 86400
        entropy = secrets.randbits(98)

        payload = (
            (sequence << (10 + 98)) |
            (millisecond << 98) |
            entropy
        )

        value = payload
        chars = []
        for _ in range(25):
            chars.append("0123456789ABCDEFGHJKMNPQRSTVWXYZ"[value & 0b11111])
            value >>= 5
        encoded = "".join(reversed(chars))

        total = 0
        for c in encoded:
            total = (total * 32 + {c: i for i, c in enumerate("0123456789ABCDEFGHJKMNPQRSTVWXYZ")}[c]) % 37

        base = encoded + "0123456789ABCDEFGHJKMNPQRSTVWXYZ*~$=U"[total]
        if not meta_used:
            return base
        
        system_s: str
        node_s: str
        id_i: int

        assert system is not None and node is not None and id is not None
        system_s = system
        node_s = node
        id_i = id

        def encode_ascii_field(text: str, out_len: int) -> str:
            data = text.encode("ascii")
            bits = int.from_bytes(data, "big")
            bitlen = len(data) * 8
            out_bits = out_len * 5

            if bitlen > out_bits:
                bits >>= (bitlen - out_bits)
            else:
                bits <<= (out_bits - bitlen)

            out = []
            for _ in range(out_len):
                out.append("0123456789ABCDEFGHJKMNPQRSTVWXYZ"[bits & 0b11111])
                bits >>= 5
            return "".join(reversed(out))

        sys_enc = encode_ascii_field(system_s, 16)
        node_enc = encode_ascii_field(node_s, 16)

        id_val = id_i
        id_chars = []
        for _ in range(6):
            id_chars.append("0123456789ABCDEFGHJKMNPQRSTVWXYZ"[id_val & 0b11111])
            id_val >>= 5
        id_enc = "".join(reversed(id_chars))

        return f"{base}${sys_enc}.{node_enc}.{id_enc}"

    @staticmethod
    def decode(uuid: str) -> dict:
        """
        Decode a Shadowflake UXID into its component fields.

        Args:
            uuid (str): The Shadowflake UXID string to decode.

        Returns:
            dict: A dictionary containing:
                - sequence (int): The rolling sequence number (0-86399)
                - millisecond (int): The millisecond component (0-999)
                - entropy (int): The random payload
                - system (str | None): Decoded SYSTEM field if present
                - node (str | None): Decoded NODE field if present
                - id (int | None): Decoded numeric ID if present
                - valid (bool): True if checksum matches, False otherwise

        Raises:
            ShadowflakeLengthError: If the core Shadowflake is not 26 characters.
            ShadowflakeChecksumError: If the checksum is invalid.
            ShadowflakeMetadataError: If metadata is malformed.
        """

        system = node = ident = None

        if "$" in uuid:
            base, meta = uuid.split("$", 1)
            parts = meta.split(".")
            if len(parts) != 3:
                raise ShadowflakeMetadataError("Invalid metadata format")

            def decode_ascii_field(text: str) -> str:
                bits = 0
                for c in text:
                    bits = (bits << 5) | {c: i for i, c in enumerate("0123456789ABCDEFGHJKMNPQRSTVWXYZ")}[c]

                byte_len = (len(text) * 5) // 8
                raw = bits.to_bytes(byte_len, "big").rstrip(b"\x00")
                return raw.decode("ascii") if raw else ""

            system = decode_ascii_field(parts[0])
            node = decode_ascii_field(parts[1])

            ident_val = 0
            for c in parts[2]:
                ident_val = (ident_val << 5) | {c: i for i, c in enumerate("0123456789ABCDEFGHJKMNPQRSTVWXYZ")}[c]
            ident = ident_val
        else:
            base = uuid

        if len(base) != 26:
            raise ShadowflakeLengthError(
                f"Shadowflake UUIDs are always 26 characters long ({len(base)} given)"
            )

        total = 0
        for c in base[:-1]:
            total = (total * 32 + {c: i for i, c in enumerate("0123456789ABCDEFGHJKMNPQRSTVWXYZ")}[c]) % 37

        if "0123456789ABCDEFGHJKMNPQRSTVWXYZ*~$=U"[total] != base[-1]:
            raise ShadowflakeChecksumError("Checksum failed")

        payload = 0
        for c in base[:-1]:
            payload = (payload << 5) | {c: i for i, c in enumerate("0123456789ABCDEFGHJKMNPQRSTVWXYZ")}[c]

        entropy = payload & ((1 << 98) - 1)
        payload >>= 98
        millisecond = payload & ((1 << 10) - 1)
        payload >>= 10
        sequence = payload & ((1 << 17) - 1)

        return {
            "sequence": sequence,
            "millisecond": millisecond,
            "entropy": entropy,
            "system": system,
            "node": node,
            "id": ident,
            "valid": True,
        }
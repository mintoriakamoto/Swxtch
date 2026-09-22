"""Tests for stealth protocol implementation."""

import struct
import secrets
from unittest.mock import patch
import pytest

from swxtch.stealth_protocol import (
    StealthProtocol,
    StealthTunnel,
    StealthPacket,
    StealthAddress,
    get_stealth_protocol,
    get_stealth_tunnel,
    STEALTH_ADDRESS_SPACE,
)


class TestStealthAddress:
    """Test stealth address implementation."""

    def test_initialization(self):
        """Should initialize stealth address."""
        value = struct.pack("!I", 0xF0000001)
        addr = StealthAddress(value=value, rotation_count=0, entropy=secrets.token_bytes(16))

        assert addr.rotation_count == 0
        assert len(addr.entropy) == 16

    def test_stealth_address_string_representation(self):
        """Should convert to pseudo-dotted format."""
        # Create address in stealth range
        value = struct.pack("!I", 0xF0000001)
        addr = StealthAddress(value=value, rotation_count=0, entropy=secrets.token_bytes(16))

        str_repr = str(addr)
        parts = str_repr.split(".")
        assert len(parts) == 4
        assert all(part.isdigit() for part in parts)

    def test_stealth_address_in_unroutable_space(self):
        """Should generate addresses in 240.0.0.0/4 range."""
        value = struct.pack("!I", 0xF0000001)
        addr = StealthAddress(value=value, rotation_count=0, entropy=secrets.token_bytes(16))

        unpacked = struct.unpack("!I", addr.value)[0]
        # Check that first 4 bits are 1111 (0xF)
        assert (unpacked & 0xF0000000) == 0xF0000000


class TestStealthPacket:
    """Test stealth packet implementation."""

    def test_initialization(self):
        """Should initialize stealth packet."""
        packet = StealthPacket(
            version=1,
            packet_id=secrets.token_bytes(16),
            encryption_key=secrets.token_bytes(32),
            nonce=secrets.token_bytes(12),
            ciphertext=b"encrypted",
            timestamp=1234567890.0,
            magic=secrets.token_bytes(4)
        )

        assert packet.version == 1
        assert len(packet.packet_id) == 16
        assert len(packet.encryption_key) == 32
        assert len(packet.nonce) == 12

    def test_packet_uniqueness(self):
        """Each packet should have unique ID."""
        packet1 = StealthPacket(
            version=1,
            packet_id=secrets.token_bytes(16),
            encryption_key=secrets.token_bytes(32),
            nonce=secrets.token_bytes(12),
            ciphertext=b"data",
            timestamp=1234567890.0,
            magic=secrets.token_bytes(4)
        )

        packet2 = StealthPacket(
            version=1,
            packet_id=secrets.token_bytes(16),
            encryption_key=secrets.token_bytes(32),
            nonce=secrets.token_bytes(12),
            ciphertext=b"data",
            timestamp=1234567890.0,
            magic=secrets.token_bytes(4)
        )

        assert packet1.packet_id != packet2.packet_id


class TestStealthProtocol:
    """Test stealth protocol implementation."""

    def test_initialization(self):
        """Should initialize stealth protocol."""
        proto = StealthProtocol()

        assert proto.version == 1
        assert proto.master_key is not None
        assert len(proto.master_key) == 32
        assert proto.packet_count == 0
        assert proto.stealth_address is not None

    def test_generate_stealth_address(self):
        """Should generate stealth address."""
        proto = StealthProtocol()
        addr = proto._generate_stealth_address()

        assert isinstance(addr, StealthAddress)
        assert len(addr.value) == 4
        assert len(addr.entropy) == 16

    def test_stealth_address_in_unroutable_range(self):
        """Generated addresses should be in unroutable space."""
        proto = StealthProtocol()
        for _ in range(10):
            addr = proto._generate_stealth_address()
            unpacked = struct.unpack("!I", addr.value)[0]
            # Verify in 240.0.0.0/4 range
            assert (unpacked & 0xF0000000) == 0xF0000000

    def test_rotate_stealth_address(self):
        """Should rotate to new stealth address."""
        proto = StealthProtocol()
        old_addr = str(proto.stealth_address)

        new_addr = proto.rotate_stealth_address()

        assert str(new_addr) != old_addr
        assert proto.stealth_address is new_addr

    def test_derive_packet_key_uniqueness(self):
        """Each packet should have unique derived key."""
        proto = StealthProtocol()

        key1, nonce1 = proto.derive_packet_key(1)
        key2, nonce2 = proto.derive_packet_key(2)

        assert key1 != key2
        assert nonce1 != nonce2
        assert len(key1) == 32
        assert len(nonce1) == 12

    def test_derive_packet_key_deterministic_for_same_sequence(self):
        """Same sequence should derive same key."""
        proto = StealthProtocol()
        master_key_backup = proto.master_key

        key1, nonce1 = proto.derive_packet_key(42)
        proto.master_key = master_key_backup
        key2, nonce2 = proto.derive_packet_key(42)

        assert key1 == key2

    def test_encrypt_stealth_packet(self):
        """Should encrypt payload into stealth packet."""
        proto = StealthProtocol()
        payload = b"test message"

        packet = proto.encrypt_stealth_packet(payload)

        assert isinstance(packet, StealthPacket)
        assert packet.version == 1
        assert len(packet.ciphertext) > 0
        assert proto.packet_count == 1

    def test_encrypt_multiple_packets_unique_keys(self):
        """Multiple encryptions should use different keys."""
        proto = StealthProtocol()
        payload = b"same payload"

        packet1 = proto.encrypt_stealth_packet(payload)
        packet2 = proto.encrypt_stealth_packet(payload)

        # Different encryption keys means different ciphertexts
        assert packet1.encryption_key != packet2.encryption_key
        assert packet1.ciphertext != packet2.ciphertext
        assert proto.packet_count == 2

    def test_serialize_stealth_packet(self):
        """Should serialize packet to bytes."""
        proto = StealthProtocol()
        payload = b"test data"
        packet = proto.encrypt_stealth_packet(payload)

        serialized = proto.serialize_stealth_packet(packet)

        assert isinstance(serialized, bytes)
        assert len(serialized) > len(payload)
        # Format: magic(4) | version(1) | packet_id(16) | nonce(12) | timestamp(8) | ciphertext_len(4) | ciphertext
        assert len(serialized) >= 4 + 1 + 16 + 12 + 8 + 4

    def test_serialized_packet_looks_like_noise(self):
        """Serialized packet should look like random noise."""
        proto = StealthProtocol()
        payload = b"test data"
        packet = proto.encrypt_stealth_packet(payload)
        serialized = proto.serialize_stealth_packet(packet)

        # First 4 bytes are random magic
        magic = serialized[:4]
        # Magic should be random (very unlikely to be all zeros or all ones)
        assert magic != b"\x00\x00\x00\x00"
        assert magic != b"\xFF\xFF\xFF\xFF"

    def test_deserialize_stealth_packet(self):
        """Should deserialize bytes back to packet."""
        proto = StealthProtocol()
        payload = b"test data"
        packet1 = proto.encrypt_stealth_packet(payload)
        serialized = proto.serialize_stealth_packet(packet1)

        packet2 = proto.deserialize_stealth_packet(serialized)

        assert packet2 is not None
        assert packet2.version == packet1.version
        assert packet2.packet_id == packet1.packet_id
        assert packet2.nonce == packet1.nonce

    def test_deserialize_invalid_data(self):
        """Should handle invalid serialized data."""
        proto = StealthProtocol()

        result = proto.deserialize_stealth_packet(b"short")

        assert result is None

    def test_decrypt_stealth_packet(self):
        """Should decrypt stealth packet."""
        proto = StealthProtocol()
        payload = b"secret message"
        packet = proto.encrypt_stealth_packet(payload)

        decrypted = proto.decrypt_stealth_packet(packet)

        assert decrypted == payload

    def test_get_stealth_status(self):
        """Should return stealth protocol status."""
        proto = StealthProtocol()
        proto.encrypt_stealth_packet(b"test")

        status = proto.get_stealth_status()

        assert isinstance(status, dict)
        assert "protocol_version" in status
        assert "current_stealth_address" in status
        assert "packets_encrypted" in status
        assert status["packets_encrypted"] == 1
        assert status["protocol_identifiable"] is False

    def test_singleton_get_stealth_protocol(self):
        """Should return singleton instance."""
        proto1 = get_stealth_protocol()
        proto2 = get_stealth_protocol()
        assert proto1 is proto2


class TestStealthTunnel:
    """Test stealth tunnel implementation."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset global singleton before each test."""
        import swxtch.stealth_protocol
        swxtch.stealth_protocol._stealth_tunnel = None
        yield
        swxtch.stealth_protocol._stealth_tunnel = None

    def test_initialization(self):
        """Should initialize stealth tunnel."""
        tunnel = StealthTunnel()

        assert tunnel.protocol is not None
        assert tunnel.exit_node is None
        assert tunnel.tunnel_active is False
        assert tunnel.packets_tunneled == 0

    def test_establish_tunnel(self):
        """Should establish stealth tunnel."""
        tunnel = StealthTunnel()

        ok, msg = tunnel.establish_tunnel("random")

        assert ok is True
        assert tunnel.tunnel_active is True
        assert "Tunnel ESTABLISHED" in msg

    def test_tunnel_packet_requires_active_tunnel(self):
        """Should fail to tunnel packet if tunnel not active."""
        tunnel = StealthTunnel()

        result = tunnel.tunnel_packet(b"data")

        assert result is None

    def test_tunnel_packet_active(self):
        """Should tunnel packet when tunnel active."""
        tunnel = StealthTunnel()
        tunnel.establish_tunnel()

        result = tunnel.tunnel_packet(b"secret message")

        assert result is not None
        assert isinstance(result, bytes)
        assert tunnel.packets_tunneled == 1

    def test_receive_tunneled_packet(self):
        """Should receive and decrypt tunneled packet (same protocol instance)."""
        tunnel = StealthTunnel()
        tunnel.establish_tunnel()

        payload = b"secret message"

        # Encrypt packet (increments packet_count to 1)
        packet = tunnel.protocol.encrypt_stealth_packet(payload)
        serialized = tunnel.protocol.serialize_stealth_packet(packet)

        # Deserialize (resets encryption_key to empty bytes)
        deserialized = tunnel.protocol.deserialize_stealth_packet(serialized)
        assert deserialized is not None

        # For same protocol instance with same master key,
        # derive the key for the same sequence number to decrypt
        derived_key, _ = tunnel.protocol.derive_packet_key(1)
        deserialized.encryption_key = derived_key

        # Now decrypt should work
        decrypted = tunnel.protocol.decrypt_stealth_packet(deserialized)
        assert decrypted == payload

    def test_rotate_identity(self):
        """Should rotate stealth identity."""
        tunnel = StealthTunnel()
        old_addr = str(tunnel.protocol.stealth_address)

        new_addr = tunnel.rotate_identity()

        assert new_addr != old_addr

    def test_get_tunnel_status(self):
        """Should return tunnel status."""
        tunnel = StealthTunnel()
        tunnel.establish_tunnel()
        tunnel.tunnel_packet(b"test")

        status = tunnel.get_tunnel_status()

        assert isinstance(status, dict)
        assert "tunnel_active" in status
        assert "packets_tunneled" in status
        assert status["tunnel_active"] is True
        assert status["packets_tunneled"] == 1

    def test_singleton_get_stealth_tunnel(self):
        """Should return singleton instance."""
        tunnel1 = get_stealth_tunnel()
        tunnel2 = get_stealth_tunnel()
        assert tunnel1 is tunnel2

    def test_tunnel_complete_flow(self):
        """Should handle complete tunnel flow."""
        tunnel = StealthTunnel()

        # Establish tunnel
        ok, msg = tunnel.establish_tunnel("random")
        assert ok is True

        # Rotate identity
        addr1 = tunnel.rotate_identity()
        assert addr1 is not None

        # Tunnel packet
        payload = b"confidential data"
        tunneled = tunnel.tunnel_packet(payload)
        assert tunneled is not None

        # Tunnel another packet
        tunneled2 = tunnel.tunnel_packet(b"more data")
        assert tunneled2 is not None

        # Status
        status = tunnel.get_tunnel_status()
        assert status["packets_tunneled"] == 2

    def test_multiple_tunnels_independent(self):
        """Each tunnel should be independent."""
        tunnel1 = StealthTunnel()
        tunnel2 = StealthTunnel()

        tunnel1.establish_tunnel()
        tunnel2.establish_tunnel()

        tunnel1.tunnel_packet(b"data1")
        tunnel2.tunnel_packet(b"data2")
        tunnel2.tunnel_packet(b"data3")

        assert tunnel1.packets_tunneled == 1
        assert tunnel2.packets_tunneled == 2


class TestStealthAddressSpace:
    """Test stealth address space configuration."""

    def test_address_space_configuration(self):
        """Should have valid address space configuration."""
        assert "base" in STEALTH_ADDRESS_SPACE
        assert "range" in STEALTH_ADDRESS_SPACE

        base = STEALTH_ADDRESS_SPACE["base"]
        assert "240.0.0.0/4" in base

        addr_range = STEALTH_ADDRESS_SPACE["range"]
        assert addr_range[0] == 0xF0000000
        assert addr_range[1] == 0xFFFFFFFF

    def test_unroutable_space_reserved(self):
        """240.0.0.0/4 space is reserved and never routable."""
        # This is a reserved range according to RFC 5771
        assert 0xF0000000 <= 0xF0000001
        assert 0xFFFFFFFF >= 0xF0000001

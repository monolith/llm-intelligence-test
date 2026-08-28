# Bramble Sensor Wire Protocol (BSWP/2.0) — Glasshouse Instruments Consortium, Technical Note TN-0044 (2020)

## 1. Purpose and scope

BSWP is a compact, half-duplex message protocol for battery-powered environmental sensors
deployed inside commercial glasshouses. It targets nodes with 32 KB of flash and no real-time
clock, connected over a shared two-wire bus of up to 400 m with as many as 96 nodes per segment.

BSWP/2.0 supersedes 1.3. The framing is deliberately unchanged so that a 1.3 gateway can pass
2.0 traffic through without understanding it; the payload registers are renumbered and are not
compatible.

Out of scope: over-the-air firmware delivery (see TN-0051), irrigation valve actuation, and any
form of encryption. BSWP assumes a physically trusted bus.

## 2. Framing

Every frame is a byte sequence:

```
+------+------+------+--------+-----------+--------+------+
| 0xB5 | LEN  | ADDR | OPCODE | PAYLOAD   | CRC16  | 0x5B |
+------+------+------+--------+-----------+--------+------+
   1      1      1       1       0..247       2       1
```

- `0xB5` start delimiter, `0x5B` end delimiter.
- `LEN` counts `ADDR` through `PAYLOAD` inclusive, so `LEN` ranges 3..250.
- `ADDR` is the node address, 0x01–0x60. `0x00` is the gateway. `0xFF` is broadcast.
- `CRC16` is CRC-16/CCITT-FALSE over `LEN` through `PAYLOAD`, transmitted big-endian.
- Byte stuffing: any `0xB5` or `0x5B` appearing inside `LEN..CRC16` is escaped as `0x7D` followed
  by the byte XOR `0x20`. `0x7D` itself is escaped the same way.

Maximum on-wire frame length after stuffing is 508 bytes. A receiver that has consumed 508 bytes
without seeing `0x5B` discards and resynchronizes on the next `0xB5`.

Bus rate is 19200 baud, 8N1. Inter-frame gap is a minimum of 3 character times (1.56 ms).

## 3. Addressing and discovery

Nodes ship with `ADDR = 0x00` (unconfigured) and a 6-byte factory serial. On power-up an
unconfigured node listens only; it never transmits unbidden.

The gateway discovers nodes with a binary-search sweep over the serial space:

1. Gateway broadcasts `OP_PROBE` (0x11) with a 6-byte prefix and a prefix length in bits.
2. Every unconfigured node whose serial matches the prefix replies after a jitter of
   `serial[5] mod 24` milliseconds with `OP_HERE` (0x12) carrying its full serial.
3. Collisions are detected by CRC failure; the gateway lengthens the prefix by one bit and
   repeats. Worst case is 48 rounds.
4. Gateway assigns an address with `OP_ADOPT` (0x13), payload = serial (6 bytes) + new `ADDR`
   (1 byte). The node writes it to flash and replies `OP_ACK`.

A node that receives `OP_ADOPT` while already addressed replies `ERR_ADOPTED` (see §6).

## 4. Register model

Each node exposes a flat register file. Registers are 16-bit addressed, 1–8 bytes wide, and
carry a type tag in their descriptor.

| reg | name | width | type | units | notes |
|---|---|---|---|---|---|
| `0x0100` | `AIR_TEMP` | 2 | int16 | 0.01 °C | −4000..8500 |
| `0x0102` | `AIR_RH` | 2 | uint16 | 0.01 % | 0..10000 |
| `0x0104` | `CO2_PPM` | 2 | uint16 | ppm | 0..40000, 0xFFFF = over-range |
| `0x0106` | `PAR` | 4 | uint32 | µmol·m⁻²·s⁻¹ ×1000 | |
| `0x0108` | `LEAF_WET` | 1 | uint8 | 0..100 | derived, not measured |
| `0x0110` | `SOIL_VWC_A` | 2 | uint16 | 0.01 % | probe A |
| `0x0112` | `SOIL_VWC_B` | 2 | uint16 | 0.01 % | probe B, 0xFFFE = absent |
| `0x0114` | `SOIL_EC` | 2 | uint16 | µS/cm | |
| `0x0200` | `BATT_MV` | 2 | uint16 | mV | |
| `0x0202` | `UPTIME_S` | 4 | uint32 | s | wraps at 2^32 |
| `0x0300` | `SAMPLE_MS` | 4 | uint32 | ms | writable, 2000..3600000 |
| `0x0302` | `REPORT_N` | 2 | uint16 | count | writable, report every N samples |
| `0x0304` | `HYST_TEMP` | 2 | uint16 | 0.01 °C | writable, default 25 |
| `0x0400` | `SERIAL` | 6 | bytes | — | read-only |
| `0x0402` | `FW_VER` | 3 | bytes | major.minor.patch | read-only |

Registers `0x0500`–`0x05FF` are reserved for vendor extension and must be ignored by generic
gateways.

## 5. Opcodes

| op | name | direction | payload |
|---|---|---|---|
| `0x11` | `OP_PROBE` | G→N | prefix[6], prefix_bits[1] |
| `0x12` | `OP_HERE` | N→G | serial[6] |
| `0x13` | `OP_ADOPT` | G→N | serial[6], addr[1] |
| `0x20` | `OP_READ` | G→N | reg[2], count[1] |
| `0x21` | `OP_READ_RSP` | N→G | reg[2], data[…] |
| `0x22` | `OP_WRITE` | G→N | reg[2], data[…] |
| `0x23` | `OP_ACK` | N→G | reg[2] |
| `0x30` | `OP_REPORT` | N→G | seq[2], reg-block per §5.1 |
| `0x31` | `OP_REPORT_ACK` | G→N | seq[2] |
| `0x40` | `OP_SYNC` | G→ALL | epoch_ms[6] |
| `0x7E` | `OP_ERR` | N→G | code[1], detail[2] |

### 5.1 Report block encoding

A report packs a run of registers as `reg_start[2]`, `reg_count[1]`, then the concatenated raw
values in register order, followed by optionally more such runs until `LEN` is exhausted. A node
may not emit more than four runs per report.

Reports are unsolicited and are sent every `REPORT_N` samples. A node retains the last 8
unacknowledged reports in RAM; on the 9th it drops the oldest and increments a saturating
counter readable at `0x0204`.

### 5.2 Time

Nodes have no clock. `OP_SYNC` carries a 48-bit millisecond epoch from the gateway; nodes store
the offset against their own uptime counter and stamp nothing. All timestamps are therefore
assigned by the gateway at receipt, with an error bounded by one inter-frame gap plus the
node's jitter, in practice under 30 ms.

## 6. Error codes

Carried in `OP_ERR` payload byte 0.

| code | name | meaning |
|---|---|---|
| `0x01` | `ERR_CRC` | CRC mismatch on the received frame |
| `0x02` | `ERR_LEN` | `LEN` inconsistent with the framing |
| `0x03` | `ERR_OPCODE` | unknown opcode |
| `0x10` | `ERR_NOREG` | register does not exist on this node |
| `0x11` | `ERR_RO` | write attempted on a read-only register |
| `0x12` | `ERR_RANGE` | value outside the register's permitted range |
| `0x13` | `ERR_WIDTH` | payload width does not match register width |
| `0x20` | `ERR_ADOPTED` | `OP_ADOPT` received by an already-addressed node |
| `0x21` | `ERR_BUSY` | sensor conversion in progress; retry after `detail` ms |
| `0x30` | `ERR_SENSOR` | probe fault; `detail` carries the register that failed |
| `0x40` | `ERR_BROWNOUT` | `BATT_MV` below 2100; node is shedding functions |

`detail` is a 16-bit little-endian field whose meaning depends on the code; where unused it is
zero.

## 7. Examples

Read air temperature and humidity from node 0x07:

```
G→N: B5 06 07 20 01 00 02 <crc> 5B      ; OP_READ reg 0x0100 count 2
N→G: B5 09 07 21 01 00 08 34 1B 58 <crc> 5B
                     ^^^^^ reg   ^^^^^ 0x0834 = 2100 = 21.00 C
                                       ^^^^^ 0x1B58 = 7000 = 70.00 %RH
```

Write a 30-second sample interval:

```
G→N: B5 08 07 22 03 00 00 00 75 30 <crc> 5B    ; 0x7530 = 30000 ms
N→G: B5 04 07 23 03 00 <crc> 5B                ; ACK
```

Attempted write of 1000 ms (below the 2000 ms floor):

```
N→G: B5 05 07 7E 12 00 03 <crc> 5B             ; ERR_RANGE, detail 0x0300
```

## 8. Conformance

A conforming gateway must implement discovery (§3), `OP_READ`/`OP_WRITE`, and report
acknowledgment. A conforming node must implement all of §5 except `OP_SYNC`, which is optional
for nodes that never emit `UPTIME_S`.

Interoperability testing is performed against the reference bus at 96 nodes, 19200 baud, with a
sustained aggregate report rate of 12 reports per second; nodes must not exceed 4 % bus
occupancy individually.

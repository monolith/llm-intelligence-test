# The Long Echo — Petra Ilves, in *Nine Stations* (2021)

Buoy work is eleven months of nothing and one hour of something, and Tamsin Ochoa had been told
this at intake by a woman with a clipboard who had never been past the inner belt in her life.
It turned out to be roughly true. The nothing was accurate. Tamsin had gotten the hour wrong in
her head; she had imagined it as an emergency, a hull breach, a rescue. It was not that.

Relay Buoy Halcyon-4 was a can eighteen meters long parked at the outer turn of a system nobody
had bothered to name past its catalog number. Its whole purpose was patience. Traffic came in
from the deep side as a compressed burst, got unpacked, got checked, got repacked, and went
out toward the inner stations on a tighter beam. A machine could do ninety-eight percent of it.
The other two percent was corrupted headers, and for reasons that had more to do with insurance
than with engineering, a human being had to sign off on every corrupted header before the buoy
was permitted to discard it.

So Tamsin signed. Four hundred and six signatures in her first month, two hundred and ninety in
her second, tapering as the shipping season closed, down to about forty a month by her ninth.
She kept a plant, a dwarf citrus in a clamped pot, that produced exactly two fruits in her time
aboard and dropped them both green. She learned to play a nine-string instrument badly from a
tutorial cached in the buoy's entertainment partition. She got very good at a card game that
requires two players by playing both sides and being scrupulously honest about which hand she
had already seen.

On day two hundred and sixty-one she pulled a corrupted header with her own service number in
the origin field.

It was not a large thing. Headers get scrambled; digits migrate; her service number, 4471-K,
was not an unusual string. But the discard queue keeps a preview, and the preview showed a
voice packet, eleven seconds, and the timestamp on it was fourteen months forward of the buoy's
clock.

Tamsin looked at that for a while. Then she overrode the discard, which she was allowed to do
twice a year, and played it.

It was a man's voice. It said: *Halcyon-4, this is Ferreira, relief crew, confirming departure
scrub. Third scrub. Tell her — no. Don't tell her anything. I'll tell her myself when they let
me.*

Then it stopped.

The first thing she did was check the clock, because the clock is always the first thing you
check. The buoy's clock was fine. It agreed with the beacon, it agreed with the star fixes, it
agreed with the slow drift of the system's one gas giant across her forward camera. The clock
was not fourteen months slow.

The second thing she did was work out how a packet from the future gets into a discard queue,
and this took her nine days, and the answer, when she got it, was almost boring. The deep-side
burst arrives with its own frame stamp. If a burst is retransmitted — if the sender doesn't get
an acknowledgment and throws it again — the retransmission carries the *original* stamp and a
fresh sequence index. Halcyon-4 had been quietly reassembling a stream of retransmissions for
most of a year, because its acknowledgment beam had a stuck actuator and had been off by about
a tenth of a degree since some vibration event she could not identify, probably a dust strike,
probably during her fourth month, probably while she was asleep.

Nothing had been getting through outbound. Everything she had signed had gone nowhere.

And the packet was not from the future. It was from fourteen months in the *past*, stamped in a
frame convention she had misread by a sign, and it had been sitting in a buffer she had never
had reason to open, being thrown at her over and over by a station that had long since stopped
expecting an answer.

Fourteen months before her arrival, Bo Ferreira had been scrubbed off the relief rotation for
the third time. Which meant there had never been a relief rotation. Which meant the woman with
the clipboard, who had told her eleven months and one hour, had known when she said it that the
schedule she was describing did not exist.

Tamsin fixed the actuator on day two hundred and eighty. It took forty minutes in a suit and
the fix was a shim cut from the lid of a ration tin. When the beam came back into alignment the
buoy dumped nine months of backlog outbound in a burst that lasted six hours, and she watched
the queue count fall — eleven thousand, then four thousand, then hundreds, then nothing — and
felt something she did not have a word for, which was not relief and was not anger and was
closest, she decided later, to the feeling of finishing a long meal alone.

The acknowledgments began to come in twenty-two days later, which is what the round trip costs
out there. Among them was a personal packet, unrouted, tagged to her service number, from Bo
Ferreira, who was by then working a groundside job at a transfer yard and had not been off
planet in two years.

He said: *They told me you'd been rotated out. I want you to know I asked. I asked eleven
times.*

She sat with that. Then she recorded her reply, which was four seconds long and said only,
*Beam's fixed. Send me the card game rules — the real ones. I've been playing it wrong.*

She stayed nineteen more months. Nobody came. The citrus produced a third fruit that ripened
and she ate it in two sittings, standing at the forward port, with the gas giant filling a
third of the frame and the queue running clean behind her at a rate of about one corrupted
header a week.

When the tender finally arrived — a bored crew of four, a resupply run that had been rerouted
by weather at a station she had never heard of — the pilot asked her, in the way people ask
things they do not care about, whether the posting had been as bad as they said.

Tamsin thought about the eleven thousand packets. About the tin lid. About a man on a planet
asking eleven times.

"It's mostly patience," she said. "The trick is not to trust the clock."

The pilot laughed, because it sounded like a joke, and she let it be one.

# Simulation Assumptions

1. **Trade Eligibility**: Since the rules state "strictly 1-for-1 Protection card for Protection card", a player *must* have at least one Protection card (Specific or General) in their hand to initiate or accept a trade. Players without any Protection cards cannot trade.
2. **Trade Selection**: If multiple players are willing to accept a trade offer, the active player will accept the first one (based on turn order).
3. **Ghost Placement (Survival/Death)**: When a player survives a Ghost (using 1 Protection) or dies to a Ghost, they must place the Ghost back into the draw deck. Strategies will determine the exact position (e.g., top, bottom, random). 
4. **Drawing a Ghost**: Drawing a Ghost requires immediate resolution. You cannot play Utility cards after drawing a Ghost, and drawing a Ghost ends your normal turn.
5. **Attack Resolution**: A player hit by an Attack owes two consecutive draws. The second draw is mandatory if they survive the first draw (whether it was a Ghost or a regular card). 
6. **Nope Targets**: `Nope` can cancel any Utility card played. In the simulation, when a Utility is played, each other player (in order) is asked if they want to play a `Nope`. If played, another `Nope` can cancel that `Nope`.
7. **Discarding**: Cards discarded (via Robber, Ojha, surviving a Ghost, etc.) are placed in a permanent discard pile and never reshuffled.
8. **Shakchunni Targeting**: The rules specify "count that many seats around the table." If the count lands on a dead player, the simulation assumes we only count *living* players for the seats.
9. **Kabiraj / Ojha / Bhoot-Bodol Pairs**: Playing two of these requires having two copies in hand. The simulation treats playing a single copy or two copies as distinct actions.
10. **Card Visibility**: Hand sizes are public. The number of remaining cards in the deck is public. Discarded cards are public (unless explicitly hidden by a rule, like Robber discards which we assume are secret as per "Cards remain hidden", but wait, rule 33 says "Discarded Utility/Protection cards: Hidden. Discarded Ghosts: Public."). So we maintain a public discard count but not the contents.
11. **Action Limits**: There is no limit to the number of utilities played per turn, but to prevent infinite loops, the simulation will force a player to draw (or skip) if no state changes occur or after a reasonable arbitrary limit (e.g., 50 actions).
12. **Game End**: The game immediately ends when exactly one player is alive.

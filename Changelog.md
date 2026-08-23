Faxit now takes fluids and gases on the later Recovery arms, unlocks line up with the shared solid, fluid and gas buildings, and two unbuildable recipes are fixed.

Hi Pioneers!

This one is a data pass over the Faxit research tree. The deeper Recovery arms now ask for fluids and gases as well as solids, unlocks grant the buildings they actually claim to grant, and two recipes that could never be built at all are repaired.

**New Content**

- Recovery deliveries now accept fluids and gases, not just solids. Each one only shows up on an arm deep enough that you can already produce it
    - Somersloop Recovery II: Water, Crude Oil, Heavy Oil Residue, Fuel
    - Somersloop Recovery III: Alumina Solution, Sulfuric Acid
    - Mercer Recovery III: Turbofuel, Nitrogen Gas
    - Somersloop Recovery IV: Nitric Acid
    - Mercer Recovery IV: Rocket Fuel
    - Somersloop Recovery V: Dark Matter Residue, Excited Photonic Matter
    - Mercer Recovery V: Ionized Fuel
- Fluid and gas deliveries start at 50 to 200 m³ and scale up to 2000 m³ across repeats, matching how solid deliveries scale
- Each Recovery node's description now names the fluids it accepts

**Progression**

- Faxit unlocks now share the solid, fluid and gas Faxit buildings instead of handing them out separately
- Renamed Remote Terminal to Terminal

**Balancing**

- Transfer speed upgrades now sit directly behind the unlock they belong to instead of deep on the main spine. Solid rates run down-left from Solid Faxing, fluid and gas rates down-right from Fluid and Gas Faxing, so you can start raising throughput as soon as you can move anything at all
- Speed upgrade costs rescaled to climb from Tier 3 to Tier 9, and every step now also asks for the Space Elevator part of its phase, from Versatile Frameworks at the first step up to AI Expansion Servers and Ballistic Warp Drives at the last
- Project parts are now something you spend rather than something you are handed. Every delivery that used to pay them out now pays Power Shards, Somersloops or Mercer Spheres instead, and the calibration gates that used to reward a project part now ask for one
- Project part amounts scale with how hard they are to make: 100 to 200 of the early ones, down to 25 to 50 of the late ones
- Alien-artifact Recovery deliveries now request at most five randomly selected items each, while keeping the full item pool available across repeats
- Every selected Recovery item now rolls a base quantity between 50 and 200 units before repeat scaling
- Every Faxit scanner and copier is now buildable in Tier 4. Faxit unlocks in Tier 3, but the processors needed Circuit Boards, and the fluid pair also needed Plastic and Rubber, all of which arrive with Oil Processing in Tier 5. The buildings that make a network do anything were stranded two tiers and a whole oil setup away
    - Circuit Boards replaced with Stators throughout
    - Plastic and Rubber in the fluid scanner and copier replaced with Rotors
- Solid Faxing and Fluid Faxing now cost 50 Stators to unlock, matching what their buildings ask for. Fluid Faxing no longer costs Plastic either, so nothing on the path to a working network needs oil

**Changes**

- Removed the obsolete Quantum Cable Adapter, along with its recipe, unlock, icon and sign-library entry. Every former use is now a Quantum Processor
- Removed the obsolete gas Faxit recipes and the Remote Access feature

**Bug Fixes**

- Fixed the Small Faxit Disk recipe asking for three solid ingredients in an Assembler, which only has two input slots. It no longer needs Steel Plates
- Fixed the Photonic Processor recipe listing its own output as an ingredient, which made Quantum Processors impossible to produce. It now uses Data Cables instead

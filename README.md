# LapSimV1 with Aero Package

This version of the LapSim (based off of the LapSimV1) incorporates downforce and drag from the aero package.

This LapSim uses multiple GG diagrams that are produced from various velocities in order to simulate the effects of downforce.

<img width="637" height="477" alt="image" src="https://github.com/user-attachments/assets/f74e5dc2-aea3-48ab-9d8a-f8518a600e3e" />

*Each color is a different velocity.

## Assumptions (related to aero)
- Uses equations that only approximate drag and downforce
<img width="201" height="52" alt="image" src="https://github.com/user-attachments/assets/c8043e20-a2d5-48e0-93a3-2d8b9dccf2f5" />

- Drag and downforce do not change with pitch or roll
- No car body angle (drag only affects the car longitudinally)
- No heave

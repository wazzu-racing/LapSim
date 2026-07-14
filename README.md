# LapSimV1 with Aero Package

This version of the LapSim (based off of the LapSimV1) incorporates downforce and drag from the aero package.

This LapSim uses multiple GG diagrams that are produced from various velocities in order to simulate the effects of downforce. After this, the maxmimum AX is capped for curves where the velocity is higher than 0. Essentially, this is mimicking the affect of drag overpowering downforce, which we cannot simulate currently because we do not have data on how downforce and drag change via pitch.

<img width="596" height="445" alt="Screenshot 2026-07-14 at 3 27 45 PM" src="https://github.com/user-attachments/assets/6a7821de-c0f9-41b2-813f-06e13da7ec7a" />

*Each color is a different velocity.

## Assumptions (related to aero)
- Uses equations that only approximate drag and downforce
<img width="201" height="52" alt="image" src="https://github.com/user-attachments/assets/c8043e20-a2d5-48e0-93a3-2d8b9dccf2f5" />

- Drag and downforce do not change with pitch or roll
- No car body angle (drag only affects the car longitudinally)
- No heave

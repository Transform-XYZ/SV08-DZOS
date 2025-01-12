
![LOGO](./documentation/images/dzos_logo.png)

# DZOS: Dynamic Z Offset and Soaking

**Latest: 0.1.36**

## GOAL:
1. Solve the SV08 bed and Z issues.
2. Dynamic Z offset based on current state of bed.
3. Dynamic pre-print soak time based on realtime bed sampling and size/duration of initial X layers.

## DISCLAIMER:
1. This is an early script, use your best judgment if it's right for you.
2. Currently only supporting the stock SV08.
3. No dynamic soaking in latest. The macro I've provided to calculate the z has an input for soak time in seconds.

## DOCUMENTATION:
[See Documentation ->](./documentation/PROCESS.md)
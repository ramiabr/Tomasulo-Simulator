                                             ‘Tomasulo Algorithm Simulator’ using Python


Configuration designed:
----------------------
There can be many variants in Tomasulo simulator, while the actual simulator designed in this project is as per specification below. These values are coded in the top portion of the code and they can be configured per requirement.
No of Execution Units:
Adder/Subtract : 3
Multiplier/Divisor : 3
Load/Store : 3
Branch : 3
No of cycles taken for ADD/SUB : 2
No of cycles taken for MUL/DIV : 20
Branch prediction : NT
No of Instruction issued per cycle : 1


Features in the design:
----------------------
 The number of execution unit in each functional unit is configurable. In the section below the Tomasulo simulator for a given set of instructions the performance of simulator is studied under various number of Execution units.
 The number of cycles each instruction takes to complete is configurable.
 The Static Branch predictor is implemented in this design and its static branch prediction outcome is configurable.
 The simulator also has a feature for running in step mode. If we provide –step 10, the simulator will execute only till 10th cycle. This gives clear picture on what is happening in each cycle.
 The flow will never run infinite loop, if for some instruction sequence the flow couldn’t converge then the simulator will exit after executing 1000 cycles.



Steps in simulator:
-------------------
 The flow parses the input options, instructions file being the required input.
 The flow sets up the scoreboard and reservation stations per the variables defined in the top portion of the code.
 While building the instruction scoreboard the flow also unrolls the loop per the static branch prediction.
 Issue each instruction in-order if the corresponding reservation station resource is available. Otherwise stall all the instructions.
 Perform execution in each of the reservation station and write to Common data bus and remove the completed instruction from the reservation station/scoreboard.



Limitation in the code:
-----------------------
There is one known limitation which couldn’t be solved in the given deadline. In the below instruction sequence, we always try to execute the instructions top to bottom so that we can resolve the dependencies from top to bottom. Now during 13th cycle of instruction sequence given below, we try to execute the 8th instruction but we realize that the execution unit is not free, so we skip and go to next instruction, when we reach the 10th instruction we realize that the current add instruction is completed and has reached CDB stage. But the flow can’t go back to start the 8th instruction which is waiting for free resource. I tried to solve this problem by going backwards one more time but it produces lot of
unwanted errors which causes complete disruption in the output printed. The vice versa of the case works successfully (i.e. if the first instruction complete it gets stricken out from scoreboards and next instruction can be scheduled in the next cycle.

S.no Instructions Issue Exec Mem CDB Commit
-------------------------------------------
7 LD R2 2(R1) 7 9 10 11 14 
8 DADDIU R2 R2 #2 8 14 16 17
9 SD R2 2(R1) 9 10 17 18 
10 DADDIU R1 R1 #8 10 11 13 19
11 BNE R2 R3 11 17 20



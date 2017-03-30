#!/usr/bin/python
import sys, getopt
import os
import re
import math
import collections


### No of Hardware resources available 
global NO_ADDERS, NO_MUL, NO_BRANCH, NO_ADDERS, NO_LD_ST
NO_ADDERS  = 3
NO_MUL     = 3 
NO_BRANCH  = 3 
NO_LD_ST   = 3 


### No of cycles each Functional Unit takes for execution 
global ADD_CYCLE, MUL_CYCLE
ADD_CYCLE  = 2
MUL_CYCLE  = 20
 
## Number of Instructions issued
## Currently code cant support ore than 1 issue
global ISSUE
ISSUE = 1


## Branch Prediction 
global BRANCH_PREDICTION
BRANCH_PREDICTION = "NT"

### Step Mode 
global step, debug 
step = 1000
debug = None


######## All global variables 
global instruction_file
global RES_ST 
RES_ST = {}

#### Execution unit 
global EXEC, INST_COUNT, INST_TRACK
EXEC = {}
INST_COUNT= 1
INST_TRACK = {}

global inst_history 
inst_history = {}



### Main function which does branchsim functionality 
def main():

    ## Parse all input options 
    parse_options()
    
    ## Initialize the Hardware 
    initialize_setup()
    
    ## Simulator
    tomasulosim()
    
    ## Display result 
    displayResult()
    

def displayResult():
	global EXEC, INST_COUNT, INST_TRACK
	
	line = '%2s %20s %10s %5s %5s %5s %5s' % ("S.no", "Instructions", "Issue", "Exec", "Mem", "CDB", "Commit")
	print line
	#print "S.no\t,Instruction\t\t\t,Issue\t,Exec\t,Mem\t,CDB"	
	#printline()

    	o = open("out.csv", "w")
	o.write("S.no,Instruction,Issue,Exec,Mem,CDB,Commit\n")
	
	for count in range(1, INST_COUNT):
		issue = "" 
		exec_i = ""
		mem  = ""
		wb = ""
		commit = ""
		
		### All ready get set to execute 
		inst = INST_TRACK[count]
				
		if(EXEC[count, inst, "issue"]):
			issue = EXEC[count, inst, "issue"]
		
		if(EXEC[count, inst, "exec"]):
			exec_i = EXEC[count, inst, "exec"]

		if(EXEC[count, inst, "mem"]):
			mem = EXEC[count, inst, "mem"]

		if(EXEC[count, inst, "wb"]):
			wb = EXEC[count, inst, "wb"]
		
		if(EXEC[count, inst, "commit"]):
			commit = EXEC[count, inst, "commit"]

		inst = re.sub(',', '', inst)
		
		line = '%2s %20s %10s %5s %5s %5s %5s' % (count, inst, issue, exec_i, mem, wb, commit)
		print line
		#print count, "\t", inst , "\t\t\t", issue, "\t", exec_i, "\t", mem, "\t", wb
		#printline()
		o.write(str(count) + "," + str(inst) + "," + str(issue) + "," + str(exec_i) + "," + str(mem) + "," + str(wb) +  str(commit) +"\n")
		
		
#def printline():
	#print "----------------------------------------------------------------"

def tomasulosim():
	global EXEC, INST_COUNT, INST_TRACK, step, debug 
	STATION_STATUS = {}
	STATION_STATUS["ADD"] = 0
	STATION_STATUS["MUL"] = 0
	STATION_STATUS["LD"] = 0
	STATION_STATUS["BRANCH"] = 0

#	LD_SD_BUSY = 0 
#	ADD_BUSY = 0
#	MUL_BUSY = 0
	BRANCH_BUSY = None
	
	clock = 0
	curr_inst = 1
	last_commit = 1
	
	while(1):
		not_ready = 0
		freeup = []
		
		#print "INFO", curr_inst, STATION_STATUS["ADD"]
		
		for count in range(1, curr_inst):
		#for count in range(curr_inst, 1, -1):
			### All ready get set to execute 
			inst = INST_TRACK[count]
			
			if(EXEC[count, inst, "done"] == 1):
				continue
	
			### Check if the source registers are ready 
			reg_d  = None
			reg1_s = None
			reg2_s = None
			
			reg_d, reg1_s, reg2_s = decode_inst(inst)
			
			#print "PROBLEM", inst, "==> ", reg1_s, reg2_s, reg_d
			
			### Check if free resource available and add, stall if required 
			avail = None
			if(EXEC[count, inst, "issue"] == None and not_ready == 0):
				avail = check_free_resource(inst, count, reg_d, reg1_s, reg2_s)

			
			if(EXEC[count, inst, "issue"] == None and avail == None):
				not_ready = 1
				continue
			
			not_ready_conflict = None
			dep = None
			
			#### Check if there are any Data Hazards 
			#if(EXEC[count, inst, "issue"] != None and EXEC[count, inst, "exec"] == None):
			if( (re.search('ld|lw|sd|sw', inst, re.IGNORECASE) and  EXEC[count, inst, "mem"] == None ) or ( re.search('add|bn|sub|mul|div', inst, re.IGNORECASE) and EXEC[count, inst, "exec"] == None) ):
				not_ready_conflict, dep = check_data_hazards(inst, count, reg_d, reg1_s, reg2_s, inst_history)
			
			if(debug and not_ready_conflict):
				print "Clock:" , clock, "Curr Inst:", inst, "Conflict:==>",  not_ready_conflict, "Dep Inst:", dep
			
			#if(EXEC[count, inst, "issue"] != None and EXEC[count, inst, "exec"] == None and busy == 1):
			#	not_ready_conflict = 1
#				continue
			
			#print clock, inst, not_ready_conflict
			if(BRANCH_BUSY != None):
				not_ready_conflict = 1
				
			#print clock, inst, BRANCH_BUSY, not_ready_conflict, STATION_STATUS["ADD"]
			
			### Check for register conflicts stall if required 			
			if(re.search('ld|lw', inst, re.IGNORECASE)):			
				##MEM To WB
				if(EXEC[count, inst, "mem"] and not_ready_conflict == None ):
					EXEC[count, inst, "wb"] = clock
					EXEC[count, inst, "done"] = 1
					#freeup_resource(count, inst)
					freeup.append(str(count) + "-" +inst)
									
				 
				## Exec to Mem
				elif(EXEC[count, inst, "exec"] ):
					EXEC[count, inst, "mem"] = clock
					STATION_STATUS["LD"] = 0

			
				## Issue to Exec
				elif(EXEC[count, inst, "issue"] and STATION_STATUS["LD"] == 0 and BRANCH_BUSY == None ):
					EXEC[count, inst, "exec"] = clock
					STATION_STATUS["LD"] = 1
			
				## Issue 
				elif(EXEC[count, inst, "issue"] == None):
					EXEC[count, inst, "issue"] = clock
					inst_history[count] = inst 
					
			### Check for register conflicts stall if required 			
			elif(re.search('sd|sw', inst, re.IGNORECASE)):			
				##MEM To WB
#				if(EXEC[count, inst, "mem"]):
#					EXEC[count, inst, "wb"] = clock
									
				 
				## Exec to Mem
				if(EXEC[count, inst, "exec"] and not_ready_conflict == None):
					EXEC[count, inst, "mem"] = clock
					STATION_STATUS["LD"] = 0
					EXEC[count, inst, "done"] = 1
					freeup.append(str(count) + "-" +inst)

			
				## Issue to Exec
				elif(EXEC[count, inst, "issue"] and STATION_STATUS["LD"] == 0  and BRANCH_BUSY == None ):
					EXEC[count, inst, "exec"] = clock
					STATION_STATUS["LD"] = 1
			
				## Issue 
				elif(EXEC[count, inst, "issue"] == None):
					EXEC[count, inst, "issue"] = clock
					inst_history[count] = inst					
			
	
			if(re.search('ADD', inst, re.IGNORECASE)):			
				 
				## Exec to Mem
				if(EXEC[count, inst, "exec"] and clock - EXEC[count, inst, "exec"] == ADD_CYCLE ):
					EXEC[count, inst, "wb"] = clock
					EXEC[count, inst, "done"] = 1			
					freeup.append(str(count) + "-" + inst)
					STATION_STATUS["ADD"] = 0
			
				## Issue to Exec
				elif(EXEC[count, inst, "issue"] and STATION_STATUS["ADD"] == 0 and not_ready_conflict == None):
				#elif(EXEC[count, inst, "issue"] and not_ready_conflict == None):
					EXEC[count, inst, "exec"] = clock
					STATION_STATUS["ADD"] = 1

					
				## Issue 
				elif(EXEC[count, inst, "issue"] == None):
					EXEC[count, inst, "issue"] = clock
					inst_history[count] = inst					

			if(re.search('SUB', inst, re.IGNORECASE)):			
				 
				## Exec to Mem
				if(EXEC[count, inst, "exec"] and clock - EXEC[count, inst, "exec"] == ADD_CYCLE ):
					EXEC[count, inst, "wb"] = clock
					EXEC[count, inst, "done"] = 1			
					freeup.append(str(count) + "-" + inst)
					STATION_STATUS["ADD"] = 0
			
				## Issue to Exec
				elif(EXEC[count, inst, "issue"] and STATION_STATUS["ADD"] == 0 and not_ready_conflict == None):
					EXEC[count, inst, "exec"] = clock
					STATION_STATUS["ADD"] = 1

					
				## Issue 
				elif(EXEC[count, inst, "issue"] == None):
					EXEC[count, inst, "issue"] = clock
					inst_history[count] = inst					

	
			if(re.search('MUL', inst, re.IGNORECASE)):			
				 
				## Exec to Mem
				if(EXEC[count, inst, "exec"] and clock - EXEC[count, inst, "exec"] == MUL_CYCLE ):
					EXEC[count, inst, "wb"] = clock
					EXEC[count, inst, "done"] = 1			
					freeup.append(str(count) + "-" + inst)
					STATION_STATUS["MUL"] = 0
			
				## Issue to Exec
				elif(EXEC[count, inst, "issue"] and STATION_STATUS["MUL"] == 0 and not_ready_conflict == None):
					EXEC[count, inst, "exec"] = clock
					STATION_STATUS["MUL"] = 1
					
				## Issue 
				elif(EXEC[count, inst, "issue"] == None):
					EXEC[count, inst, "issue"] = clock
					inst_history[count] = inst					

			if(re.search('DIV', inst, re.IGNORECASE)):			
				 
				## Exec to Mem
				if(EXEC[count, inst, "exec"] and clock - EXEC[count, inst, "exec"] == MUL_CYCLE ):
					EXEC[count, inst, "wb"] = clock
					EXEC[count, inst, "done"] = 1			
					freeup.append(str(count) + "-" + inst)
					STATION_STATUS["MUL"] = 0
			
				## Issue to Exec
				elif(EXEC[count, inst, "issue"] and STATION_STATUS["MUL"] == 0 and not_ready_conflict == None):
					EXEC[count, inst, "exec"] = clock
					STATION_STATUS["MUL"] = 1
					
				## Issue 
				elif(EXEC[count, inst, "issue"] == None):
					EXEC[count, inst, "issue"] = clock
					inst_history[count] = inst					
	
	
			if(re.search('BNE', inst, re.IGNORECASE)):			
				 
				## Issue to Exec
				if(EXEC[count, inst, "issue"] and not_ready_conflict == None):
					EXEC[count, inst, "exec"] = clock
					EXEC[count, inst, "done"] = 1
					freeup.append(str(count) + "-" + inst)
					BRANCH_BUSY = 1
					#continue
			
				## Issue 
				if(EXEC[count, inst, "issue"] == None):
					EXEC[count, inst, "issue"] = clock
					inst_history[count] = inst					
			
			
		

		#print "\n\n"
		clock += 1
	
				
		if(freeup):
			for freeup_i in freeup:
				count, inst = re.split("-", freeup_i)
				#print "RESET:", count, inst
				freeup_resource(count, inst)
				#global RES_ST
				#print "INFO",  RES_ST[inst, int(count), "inst"]
				#print RES_ST
				inst_history[int(count)] = None	
		
		BRANCH_BUSY = None		
		
		freeup = []
			
		if(curr_inst < INST_COUNT and not_ready == 0):	
			curr_inst += 1

		#not_ready = 0

		done = check_all_done()
		
		if(done == 1):
			break
		
		if(clock > int(step)):
			displayResult()
			if(int(step) > 100):
				print "\n**************************************"
				print "ERROR: simulator did not converge"
				print "**************************************"
			sys.exit(-1)
			
			
	#### Iterate through the instruction
	last_val = 1 
	for count in INST_TRACK.keys():			 
		#print key
		inst = INST_TRACK[count]
		

		if(EXEC[count, inst, "wb"] > 0):
			if(last_val > EXEC[count, inst, "wb"] + 1) :
				EXEC[count, inst, "commit"] = last_val + 1
				last_val = EXEC[count, inst, "commit"] 
			else:
				EXEC[count, inst, "commit"] = EXEC[count, inst, "wb"] + 1
				last_val = EXEC[count, inst, "commit"] 		
		elif(EXEC[count, inst, "mem"] > 0):
			if(last_val > EXEC[count, inst, "mem"] + 1) :
				EXEC[count, inst, "commit"] = last_val + 1
				last_val = EXEC[count, inst, "commit"] 
			else:
				EXEC[count, inst, "commit"] = EXEC[count, inst, "mem"] + 1
				last_val = EXEC[count, inst, "commit"] 
		elif(EXEC[count, inst, "exec"] > 0):
			if(last_val > EXEC[count, inst, "exec"] + 1) :
				EXEC[count, inst, "commit"] = last_val + 1
				last_val = EXEC[count, inst, "commit"] 
			else:
				EXEC[count, inst, "commit"] = EXEC[count, inst, "exec"] + 1
				last_val = EXEC[count, inst, "commit"] 
						

 
def check_data_hazards(inst, count, reg_d, reg1_s, reg2_s, inst_history):
	global RES_ST
	busy = None
	dep = None
	tmp = None
	
	#print inst, type(inst_history)
	# count , inst_history
	#print "\n\n"
	
	
	for ref_inst in inst_history:
		if(inst_history[ref_inst] == None or int(ref_inst) == int(count)):
			continue
			
		#print inst_history[ref_inst]
		ref_reg_d, ref_reg1_s, ref_reg2_s  = decode_inst(inst_history[ref_inst])
		
		#print count, reg1_s, reg2_s, reg_d
		if( int(count) > int(ref_inst) and (ref_reg_d == reg1_s or ref_reg_d == reg1_s)):
			busy = 1
			dep  = inst_history[ref_inst]
			tmp = ref_inst
		#print "\n\n"
		
		## If there is a branch instruction, all instructions below should be stalled
		if(int(count) > int(ref_inst) and re.search("bn", inst_history[ref_inst], re.IGNORECASE)):
			busy = 1
			dep  = inst_history[ref_inst]
			tmp = ref_inst
		
	
	#print count, inst, "Busy: ", busy, "==>", inst_history
	##print "Reason:", dep, "PROBLEM: ", count, ">", tmp
	#print "\n\n"
		
	
	return ([busy, dep])
	
	
	

def check_free_resource(inst, count, reg_d, reg1_s, reg2_s):
	global RES_ST
	avail = None
	
	## Load reservation station 
	if(re.search('ld|lw', inst, re.IGNORECASE)):
		fu = "LD"
		for i in range(0, NO_LD_ST):
			#print "PROBLEM", count, inst, RES_ST[fu, i, "inst"], "==>", i
			if(RES_ST[fu, i, "inst"] == None):
				RES_ST[fu, i, "inst"] = inst
				RES_ST[fu, i, "count"]  = count
				RES_ST[fu, i, "reg1_s"] = reg1_s
				RES_ST[fu, i, "reg2_s"] = reg2_s
				RES_ST[fu, i, "reg_d"]  = reg_d
				avail = 1
				return (avail)	
		return avail

	## Store reservation station
	if(re.search('sd|sw', inst, re.IGNORECASE)):
		fu = "SD"
		for i in range(0, NO_LD_ST):
			if(RES_ST[fu, i, "inst"] == None):
				RES_ST[fu, i, "inst"] = inst
				RES_ST[fu, i, "count"]  = count
				RES_ST[fu, i, "reg1_s"] = reg1_s
				RES_ST[fu, i, "reg2_s"] = reg2_s
				RES_ST[fu, i, "reg_d"]  = reg_d
				avail = 1
				return (avail)	

	## ADD|SUB reservation station
	if(re.search('ADD|SUB', inst, re.IGNORECASE)):
		fu = "ADD"
		for i in range(0, NO_ADDERS):
			if( RES_ST[fu, i, "inst"] == None):
				RES_ST[fu, i, "inst"] = inst
				RES_ST[fu, i, "count"]  = count
				RES_ST[fu, i, "reg1_s"] = reg1_s
				RES_ST[fu, i, "reg2_s"] = reg2_s
				RES_ST[fu, i, "reg_d"]  = reg_d
				avail = 1
				return (avail)	
				
	## MUL reservation station
	if(re.search('MUL|DIV', inst, re.IGNORECASE)):
		fu = "MUL"
		for i in range(0, NO_MUL):
			if(RES_ST[fu, i, "inst"] == None):
				RES_ST[fu, i, "inst"] = inst
				RES_ST[fu, i, "count"]  = count
				RES_ST[fu, i, "reg1_s"] = reg1_s
				RES_ST[fu, i, "reg2_s"] = reg2_s
				RES_ST[fu, i, "reg_d"]  = reg_d
				avail = 1
				return (avail)	
				

	## Branch reservation station
	if(re.search('BN', inst, re.IGNORECASE)):
		fu = "BRANCH"
		for i in range(0, NO_BRANCH):
			if(RES_ST[fu, i, "inst"] == None):
				RES_ST[fu, i, "inst"] = inst
				RES_ST[fu, i, "count"]  = count
				RES_ST[fu, i, "reg1_s"] = reg1_s
				RES_ST[fu, i, "reg2_s"] = reg2_s
				RES_ST[fu, i, "reg_d"]  = reg_d
				avail = 1
				return (avail)	
				
	
	return (avail)		
		 
		


def check_all_done():
	global EXEC, INST_COUNT, INST_TRACK
	done = 1
	
	for count in range(1, INST_COUNT):
		inst = INST_TRACK[count]
		
		if(EXEC[count, inst, "done"] == None):
			done = 0	
	
	return done


### Create the hardware setup which contains 
def initialize_setup():
	global RES_ST 
	
	## Build Reservation Station 
	build_resrvation_scoreboard()
	
	## Build Execution Hash 
	build_inst_scoreboard()
	

def build_resrvation_scoreboard():
	global RES_ST

	## Data structure for 
	for i in range(0, NO_LD_ST):
		reset_res_st("LD", i)
		reset_res_st("SD", i)
		 
	## Data structure for 
	for i in range(0, NO_ADDERS):
		reset_res_st("ADD", i)

	## Data structure for 
	for i in range(0, NO_MUL):
		reset_res_st("MUL", i)

	## Data structure for 
	for i in range(0, NO_BRANCH):
		reset_res_st("BRANCH", i)


def freeup_resource(count, inst):
	global RES_ST

	## Load reservation station 
	if(re.search('ld|lw', inst, re.IGNORECASE)):
		fu = "LD"
		for i in range(0, NO_LD_ST):
			if(RES_ST[fu, i, "inst"] == inst and RES_ST[fu, i, "count"] == int(count)):
				reset_res_st(fu, i)
					

	## Store reservation station
	if(re.search('sd|sw', inst, re.IGNORECASE)):
		fu = "SD"
		for i in range(0, NO_LD_ST):
			if(RES_ST[fu, i, "inst"] == inst and RES_ST[fu, i, "count"] == int(count)):
				reset_res_st(fu, i)

	## ADD|SUB reservation station
	if(re.search('ADD|SUB', inst, re.IGNORECASE)):
		fu = "ADD"
		for i in range(0, NO_ADDERS):
			if(RES_ST[fu, i, "inst"] == inst and RES_ST[fu, i, "count"] == int(count)):
				reset_res_st(fu, i)	
				
	## MUL reservation station
	if(re.search('MUL|DIV', inst, re.IGNORECASE)):
		fu = "MUL"
		for i in range(0, NO_MUL):
			if(RES_ST[fu, i, "inst"] == inst and RES_ST[fu, i, "count"] == int(count)):
				reset_res_st(fu, i)
				

	## Branch reservation station
	if(re.search('BN', inst, re.IGNORECASE)):
		fu = "BRANCH"
		for i in range(0, NO_BRANCH):
			if(RES_ST[fu, i, "inst"] == inst and RES_ST[fu, i, "count"] == int(count)):
				reset_res_st(fu, i)
				
	


def reset_res_st(fu, no):
	global RES_ST

	RES_ST[fu, no, "inst"]   = None
	RES_ST[fu, no, "count"]  = None
	RES_ST[fu, no, "reg1_s"] = None
	RES_ST[fu, no, "reg2_s"] = None
	RES_ST[fu, no, "reg_d"]  = None
		 
		
	


def build_inst_scoreboard():
	global instruction_file, BRANCH_PREDICTION, EXEC, INST_COUNT, RES_ST
	#inst_counter = 1
	#instructions = []
	
	## Read the instructions file
	with open(instruction_file) as f:
    		lines = f.read().splitlines()
	
	instructions = lines
	string = str.join(";", lines)
	
	pattern = re.search(':', string)
	if(pattern):
        	if(BRANCH_PREDICTION == "NT"):
        		loop_pattern = re.search('\s*(\S+)\s*:', string)
        		jump_name = loop_pattern.group(1)
        		new_string = re.sub('\s*' + jump_name + '\s*:' , '', string)
        		new_string = re.sub(',\s*' + jump_name , '', new_string)
        		instructions = new_string.split(';')
        		#print instructions
        	else:
        		accum = list()
        		master_list = list()
        		for line in lines:
        			line = re.sub('\s*LOOP\s*:' , '', line)					
        			loop_pattern = re.search(',\s*LOOP\s*$', line)
        			
        			if(loop_pattern):	
        				line = re.sub(',\s*LOOP\s*$' , '', line)			
        				master_list.extend(accum)
        				master_list.append(line)
        				master_list.extend(accum)
        				master_list.append(line)
        				master_list.extend(accum)
        				master_list.append(line)
        				master_list.extend(accum)
        				master_list.append(line)
        				
        								
        				accum = list()
        			
        			else:
        				#print accum
        				accum.append(line)
		
		#print master_list
		#sys.exit(-1)
		
		
			string = str.join(";", master_list)
			new_string = re.sub('\w*.*:' , '', string)		
			instructions = new_string.split(';')
		
		#print master_list
		
#sys.exit(-1)


	### Build scoreboard for Instructions 
	for inst in instructions:
		if(re.search('^\s*$', inst)):
			continue 
	
		inst = re.sub('^\s*', '', inst)
		reg_d, reg1_s, reg2_s = decode_inst(inst)

		EXEC[INST_COUNT, inst, "done"] = None		
		EXEC[INST_COUNT, inst, "issue"] = None
		EXEC[INST_COUNT, inst, "exec"]  = None
		EXEC[INST_COUNT, inst, "mem"]   = None
		EXEC[INST_COUNT, inst, "wb"]    = None
		EXEC[INST_COUNT, inst, "commit"]    = None
		
		#INST_TRACK.append(str(inst_counter)+"--"+inst)
		INST_TRACK[INST_COUNT] =  inst
		
				
		INST_COUNT += 1
	
	#print EXEC
	

def decode_inst(inst):
	reg_d  = None 
	reg1_s = None
	reg2_s = None
	
	regex_pattern = re.search('ld\s+(\S+)\s*,\s*(\S+)\((\S+)\)', inst, re.IGNORECASE)
	if(regex_pattern):
		reg_d = regex_pattern.group(1)
            	add_d = regex_pattern.group(2)
        	reg1_s = regex_pattern.group(3)
		reg2_s = None
		return (reg_d, reg1_s, reg2_s)

	regex_pattern = re.search('lw\s+(\S+)\s*,\s*(\S+)\((\S+)\)', inst, re.IGNORECASE)
	if(regex_pattern):
		reg_d = regex_pattern.group(1)
            	add_d = regex_pattern.group(2)
        	reg1_s = regex_pattern.group(3)
		reg2_s = None
		return (reg_d, reg1_s, reg2_s)

	regex_pattern = re.search('ADD\w*\s+(\S+)\s*,\s*(\S+)\s*,\s*(\S+)', inst, re.IGNORECASE)
	if(regex_pattern):
		reg_d  = regex_pattern.group(1)
        	reg1_s = regex_pattern.group(2)
		reg2_s = regex_pattern.group(3)
		
		if(re.search('\#', reg2_s)):
			reg2_s = None
			
		return (reg_d, reg1_s, reg2_s)

	regex_pattern = re.search('SUB\w*\s+(\S+)\s*,\s*(\S+)\s*,\s*(\S+)', inst, re.IGNORECASE)
	if(regex_pattern):
		reg_d  = regex_pattern.group(1)
        	reg1_s = regex_pattern.group(2)
		reg2_s = regex_pattern.group(3)
		
		if(re.search('\#', reg2_s)):
			reg2_s = None
			
		return (reg_d, reg1_s, reg2_s)

	regex_pattern = re.search('MUL\w*\s+(\S+)\s*,\s*(\S+)\s*,\s*(\S+)', inst, re.IGNORECASE)
	if(regex_pattern):
		reg_d  = regex_pattern.group(1)
        	reg1_s = regex_pattern.group(2)
		reg2_s = regex_pattern.group(3)
		
		if(re.search('\#', reg2_s)):
			reg2_s = None
			
		return (reg_d, reg1_s, reg2_s)

	regex_pattern = re.search('DIV\w*\s+(\S+)\s*,\s*(\S+)\s*,\s*(\S+)', inst, re.IGNORECASE)
	if(regex_pattern):
		reg_d  = regex_pattern.group(1)
        	reg1_s = regex_pattern.group(2)
		reg2_s = regex_pattern.group(3)
		
		if(re.search('\#', reg2_s)):
			reg2_s = None
			
		return (reg_d, reg1_s, reg2_s)

		
	regex_pattern = re.search('sd\s+(\S+)\s*,\s*(\S+)\((\S+)\)', inst, re.IGNORECASE)
	if(regex_pattern):
		#reg_d = regex_pattern.group(3)
		reg_d = None
            	add_d = regex_pattern.group(2)
        	reg1_s = regex_pattern.group(1)
		reg2_s = regex_pattern.group(2)
		return (reg_d, reg1_s, reg2_s)

	regex_pattern = re.search('sw\s+(\S+)\s*,\s*(\S+)\((\S+)\)', inst, re.IGNORECASE)
	if(regex_pattern):
		#reg_d = regex_pattern.group(3)
		reg_d = None
            	add_d = regex_pattern.group(2)
        	reg1_s = regex_pattern.group(1)
		reg2_s = regex_pattern.group(2)
		return (reg_d, reg1_s, reg2_s)

	regex_pattern = re.search('BNE\w*\s+(\S+)\s*,\s*(\S+)\s*', inst, re.IGNORECASE)
	if(regex_pattern):
		reg_d  = None
        	reg1_s = regex_pattern.group(1)
		reg2_s = regex_pattern.group(2)
				
		return (reg_d, reg1_s, reg2_s)
		
	print "ERROR: Unrecognized instruction ", inst 
	print "Support needs to be added in the script before this type of instruction can be processed"
	sys.exit(-1)

	return (reg_d, reg1_s, reg2_s)
	
	

## parse_options function pareses command line options 
## verifies if there are in line with expectation 
def parse_options(): 
    global instruction_file, step, debug 
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:ifile",  ["ifile=", "h=", "step=", "debug"])
    except getopt.GetoptError as err:
        print str(err)
        usage()

    all_options = [] 
    mode = ""
    
    for key, value in opts:
        all_options.append(key)    
        
	if("--ifile" in key):
            instruction_file = value 
            if(not os.path.isfile(value)):
                print "ERROR: Couldn't read instructions file \"", value ,"\"(Please check if the file exists) \n" 
                sys.exit(-1) 
	elif("--step" in key):
            step = value 
	elif("--debug" in key):
            debug = 1
    		

    ## Check for required options
    if("--ifile" not in all_options):
        print ""
        print "ERROR: Please provide --ifile <Instructions file> as input"
        usage()
     

    print "\nINFO: Input sanity check passed proceeding with tomasulo"   



## Print Usage information to user and exit 
def usage(): 
    print "Usage: " , sys.argv[0] , " --ifile <Instruction file> "
    print "--------------------------------------------------------------"
    print "--ifile  = Provide a file containing Assembly MIPS Instructions"
    print ""
    print "Optional:"
    print "--step 10 = Executes the flow till 10th cycle, this comes in handy for debug"
    print " ", sys.argv[0] ,"  --ifile file "
    sys.exit(2)

if __name__ == "__main__":
    main()  

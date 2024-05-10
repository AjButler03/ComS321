# Andrew Butler ajbutler@iastate.edu
# Com S 321 Programming assignment 2
# Due april 25, 2024

# Goal: given a compiled legv8 machine file, read bytes and 'de-compile' the code

import argparse

# For referance: Python bitwise operators
# & Bitwise AND
# | Bitwise OR
# ^ Bitwise XOR
# ~ Bitwise NOT
# << Bitwise left shift
# >> Bitwise right shift

# string used to store completed instructions
output_code = ""

# takes a register number and translates it to a string; 
# i.e., 2 => X2 or 31 => XZR
def reg_str(x):
    if (((x >= 0) and (x <= 15)) or ((x >= 18) and (x <= 27))):
        return "X" + str(x)
    elif (x == 16):
        return "IP0"
    elif (x == 17):
        return "IP1"
    elif (x == 28):
        return "SP"
    elif (x == 29):
        return "FP"
    elif (x == 30):
        return "LR"
    elif (x == 31):
        return "XZR"
    else:
        # shouldn't happen, so just writing it as if it's a register
        return "Error: X" + str(x) + " (?)"

# small function that takes computes two's complement value for a field of length numBits
# storing the bitpattern that represents int val
def twos_comp(val, numBits):
    if (val & (1 << (numBits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << numBits)        # compute negative value
    return val                            # return positive value as is

# create string for R-type instruction {name} on line {line}, reading from int {inst}
# returns string of instruction
def r_type(line, opcode, name, instr):
    # shifting bits right until field is the furthest right bits, then bit masking using AND
    rm = instr >> 16 # shifting so rm field is the rightmost 5 bits
    rm = rm & 31 # masking all but rightmost 5 bits
    shamt = instr >> 10 # shifting so that 
    shamt = shamt & 63 # masking all but the rightmost 6 bits
    rn = instr >> 5
    rn = rn & 31 # masking all but rightmost 5 bits
    rd = instr & 31
    
    # check for special cases; PRNT, BR, PRNL, DUMP, HALT
    if (opcode == 2044 or opcode == 2046 or opcode == 2047):
        # PRNL, DUMP, or Halt; no registers needed
        return f'{line}: {name}'
    elif (opcode == 1712 or opcode == 2045):
        # either BR or PRNT
        if (opcode == 1712):
            # because of course it is, br uses a different register for it's field than PRNT.
            return f'{line}: {name} {reg_str(rn)}'
        return f'{line}: {name} {reg_str(rd)}'
    else:
        # regular R-type instruction; returning string in that format
        return f'{line}: {name} {reg_str(rd)}, {reg_str(rn)}, {reg_str(rm)}'

# create string for I-type instruction {name} on line {line}, reading from int {inst}
# returns string of instruction
def i_type(line, opcode, name, instr):
    immediate = instr >> 10 # shifting right so that the immediate field is the rightmost 12 bits
    immediate = immediate & 4095 # masking all but rightmost 12 bits (immediate field)
    immediate = twos_comp(immediate, 12) # calculating two's comp value
    rn = instr >> 5 # shifting right so that the rn field is the rightmost bits
    rn = rn & 31 # masking all but rightmost 5 bits (rn field)
    rd = instr & 31 # masking all but rightmost 5 bits (rd field)
    return f'{line}: {name} {reg_str(rd)}, {reg_str(rn)}, #{immediate}'

# create string for B-type instruction {name} on line {line}, reading from int {inst}
# returns string of instruction
def b_type(line, opcode, name, instr):
    # this is definitely not correct
    address_offset = instr & 67108863 # masking all but the rightmost 26 bits (address field)
    address_offset = twos_comp(address_offset, 26)
    address = line + address_offset
    return f'{line}: {name} {address}'

# create string for CB-type instruction {name} on line {line}, reading from int {inst}
# returns string of instruction
def cb_type(line, opcode, name, instr):
    address = instr >> 5 # make address the rightmost 19 bits
    address = address & 524287 # mask all but rightmost 19 bits (address field)
    address = line + twos_comp(address, 19)
    rt = instr & 31 # mask all but rightmost 5 bits (rt field)
    
    # check if CBZ or CBNZ
    if (opcode >= 1440 and opcode <= 1455):
        return f'{line}: {name} {reg_str(rt)}, {address}'
    else: # must be b.cond
        # based on rt field, get cond
        cond = ''
        if (rt == 0):
            cond = 'EQ'
        elif (rt == 1):
            cond = 'NE'
        elif (rt == 2):
            cond = 'HS'
        elif (rt == 3):
            cond = 'LO'
        elif (rt == 4):
            cond = 'MI'
        elif (rt == 5):
            cond = 'PL'
        elif (rt == 6):
            cond = 'VS'
        elif (rt == 7):
            cond = 'VC'
        elif (rt == 8):
            cond = 'HI'
        elif (rt == 9):
            cond = 'LS'
        elif (rt == 10):
            cond = 'GE'
        elif (rt == 11):
            cond = 'LT'
        elif (rt == 12):
            cond = 'GT'
        elif (rt == 13):
            cond = 'LE'
    return f'{line}: {name}{cond} {address}'
        

# create string for D-type instruction {name} on line {line}, reading from int {inst}
# returns string of instruction
def d_type(line, opcode, name, instr):
    address = instr >> 12 # shifting right to make address rightmost bits
    address = address & 511 # masking all but rightmost 9 bits (address field)
    address = twos_comp(address, 9)
    rn = instr >> 5 # shifting right to make rn field rightmost bits
    rn = rn & 31 # masking all but 5 rightmost bits (rn field)
    rt = instr & 31 # masking all but 5 rightmost bits (rt field)
    
    return f'{line}: {name} {reg_str(rt)}, [{reg_str(rn)}, #{address}]'


# Begin Main ---------------------------------------------------------------------------------------

# parsing argument for file name
parser = argparse.ArgumentParser()
parser.add_argument("fileName", help="Name of the the file to read data from", type=str)
args = parser.parse_args()

# print filename that we are reading from
print("reading file: "+ args.fileName)
# opening file in bitwise mode
f = open(args.fileName, mode="rb")
data = f.read() # reading file
f.close # closing data reader

print(type(data)) # Note: we are reading data of class 'bytes'; not str.

# getting total number of instructions
length = int(data.__len__() / 4) # 4 bytes to instruction
# Printing number of instructions
print("Number of instructions: " + str(length))

f = open(args.fileName, mode="rb") # reopening data reader
# loop through data for the number of instructions; read 4 bytes at a time
for i in range(length):
    instruction_data = f.read(4) # reading 4 bytes for 32-bit instruction
    instr_int = 0
    for byte in instruction_data:
        temp = instr_int << 8 # LSL by 8 bits to allow new byte to be added
        instr_int = temp | byte # fill in rightmost 8 bits with new byte
    opcode = instr_int >> 21 #LSR bits by 21 to get just the 11 bit opcode
    # print(f'Opcode: {opcode}') # print opcode for testing
    
    # depending on opcode, figure out which string construction function to call, then appending to output_code
    # Note: maybe there is a better way to do this (dict?), but I'll just do it this way. I just really love if statements.
    # Note 2: ordered as they are ordered in the pa2 spec on Piazza, so it's not completely random. Just looks that way.
    if (opcode == 1112):
        # ADD
        output_code += r_type(i+1, opcode, "ADD", instr_int)
    elif (opcode == 1160 or opcode == 1161):
        # ADDI
        output_code += i_type(i+1, opcode, "ADDI", instr_int)
    elif (opcode == 1104):
        # AND
        output_code += r_type(i+1, opcode, "AND", instr_int)
    elif (opcode == 1168 or opcode == 1169):
        # ANDI
        output_code += i_type(i+1, opcode, "ANDI", instr_int)
    elif (opcode >= 160 and opcode <= 191):
        # B
        output_code += b_type(i+1, opcode, "B", instr_int)
    elif (opcode >= 672 and opcode <= 679):
        # B.cond; cond will be determined in cb_type function
        output_code += cb_type(i+1, opcode, "B.", instr_int)
    elif (opcode >= 1184 and opcode <= 1215):
        # BL
        output_code += b_type(i+1, opcode, "BL", instr_int)
    elif (opcode == 1712):
        # BR
        output_code += r_type(i+1, opcode, "BR", instr_int)
    elif (opcode >= 1448 and opcode <= 1455):
        # CBNZ
        output_code += cb_type(i+1, opcode, "CBNZ", instr_int)
    elif (opcode >= 1440 and opcode <= 1447):
        # CBZ
        output_code += cb_type(i+1, opcode, "CBZ", instr_int)
    elif (opcode == 1616):
        # EOR
        output_code += r_type(i+1, opcode, "EOR", instr_int)
    elif (opcode == 1680 or opcode == 1681):
        # EORI
        output_code += i_type(i+1, opcode, "EORI", instr_int)
    elif (opcode == 1986):
        # LDUR
        output_code += d_type(i+1, opcode, "LDUR", instr_int)
    elif (opcode == 1691):
        # LSL
        output_code += r_type(i+1, opcode, "LSL", instr_int)
    elif (opcode == 1690):
        # LSR
        output_code += r_type(i+1, opcode, "LSR", instr_int)
    elif (opcode == 1360):
        # ORR
        output_code += r_type(i+1, opcode, "ORR", instr_int)
    elif (opcode == 1424 or opcode == 1425):
        # ORRI
        output_code += i_type(i+1, opcode, "ORRI", instr_int)
    elif (opcode == 1984):
        # STUR (literally 1984)
        output_code += d_type(i+1, opcode, "STUR", instr_int)
    elif (opcode == 1624):
        # SUB
        output_code += r_type(i+1, opcode, "SUB", instr_int)
    elif (opcode == 1672 or opcode == 1673):
        # SUBI
        output_code += i_type(i+1, opcode, "SUBI", instr_int)
    elif (opcode == 1928 or opcode == 1929):
        # SUBIS
        output_code += i_type(i+1, opcode, "SUBIS", instr_int)
    elif (opcode == 1880):
        # SUBS
        output_code += r_type(i+1, opcode, "SUBS", instr_int)
    elif (opcode == 1240):
        # MUL
        output_code += r_type(i+1, opcode, "MUL", instr_int)
    elif (opcode == 2045):
        # PRNT
        output_code += r_type(i+1, opcode, "PRNT", instr_int)
    elif (opcode == 2044):
        # PRNL
        output_code += r_type(i+1, opcode, "PRNL", instr_int)
    elif (opcode == 2046):
        # DUMP
        output_code += r_type(i+1, opcode, "DUMP", instr_int)
    elif (opcode == 2047):
        # HALT
        output_code += r_type(i+1, opcode, "HALT", instr_int)
    else:
        # opcode not recognized; printing an error message
        temp = i+1
        output_code += f'{temp}: //ERROR: Opcode {opcode} not recognized'
    if (i < length -1): # determine if newline character is needed or not
        output_code += '\n'
f.close
print(output_code)
from PIL import Image, ImageOps
import numpy as np
from numpy.polynomial import Polynomial
import re
import reedsolo
import textwrap as tw
import binascii
import sys
import cv2

np.set_printoptions(threshold=sys.maxsize)

inputText = '0123456789'

print(len(inputText))

#test reed-solomon
'''
inputTextBytes = list(inputText.encode('iso-8859-1'))
print("Message as array:", inputTextBytes)
rsc = reedsolo.RSCodec(10)
test2 = rsc.encode(inputTextBytes)
test4 = test2[(len(inputText)):]
test5 = test4.decode('iso-8859-1')
test6 = bin(int(test4.hex(), 16))[2:].zfill(8)
test7 = binascii.unhexlify(test4.hex())
print('t4hex', test4.hex())
print('t4', test4)
print('t5', test5)
print('t6', test6)
print('t7', test7)

for i in test4:
    print(i, type(i))
'''
# alphanumeric table

alNumTable = {"0": "0",	"1": "1",	"2": "2",	"3": "3",	"4": "4",	"5": "5",	"6": "6",	"7": "7",	"8": "8",	"9": "9",	"10": "A",	"11": "B",	"12": "C",	"13": "D",	"14": "E",	"15": "F",	"16": "G",	"17": "H",	"18": "I",	"19": "J",	"20": "K",	"21": "L",	"22": "M",	"23": "N",	"24": "O",	"25": "P",	"26": "Q",	"27": "R",	"28": "S",	"29": "T",	"30": "U",	"31": "V",	"32": "W",	"33": "X",	"34": "Y",	"35": "Z",	"36": "",	"37": "$",	"38": "%",	"39": "*",	"40": "+",	"41": "-",	"42": ".",	"43": "/",	"44": ":"}

#regex pattern
pattern = re.compile("[A-Z0-9\s$+:'\/'.%*--]")

#Error correction level chosen = L, as it's only a small project we'll cover only first five versions
numericMode = {"1": "41", "2": "77", "3": "127", "4": "187", "5": "255"}

alphanumericMode = {"1": "25", "2": "47", "3": "77", "4": "114", "5": "154"}

byteMode = {"1": "17", "2": "32", "3": "53", "4": "78", "5": "106"}



#check mode
mode = ''
if inputText.isdigit():
    mode = 0b0001
elif pattern.search(inputText) and inputText.isupper():
    mode = 0b0010
elif inputText.encode('iso-8859-1'):
    try:
       mode = 0b0100
    except UnicodeEncodeError:
        print('Unable to handle one of the characters')

#Character Count Indicator and version

count = len(inputText)
binaryCount = np.binary_repr(count)
cci = ''
version = ''
if mode == 1:
    cci = binaryCount.zfill(10)
    for key, value in numericMode.items():
        if int(value) >= count:
            version = key
            break
elif mode == 2:
    cci = binaryCount.zfill(9)
    for key, value in alphanumericMode.items():
        if int(value) >= count:
            version = key
            break
elif mode == 4:
    cci = binaryCount.zfill(8)
    for key, value in byteMode.items():
        if int(value) >= count:
            version = key
            break

#Step 3: Encode Using the Selected Mode
encData = list()
if mode == 1:
    splitString = tw.wrap(inputText, 3)
    for i in splitString:
        if i != splitString[-1] and i[0] == '0' and i[1] != '0':
            splitStringBinary = np.binary_repr(int(i[1:])).zfill(7)
            
        elif i != splitString[-1] and i[0] == '0' and i[1] == '0':
            splitStringBinary = np.binary_repr(int(i[2:])).zfill(4)
            
        elif i == splitString[-1] and len(splitString[-1]) == 2:
            splitStringBinary = np.binary_repr(int(i[-1])).zfill(7)
            
        elif i == splitString[-1] and len(i[-1]) == 1:
            splitStringBinary = np.binary_repr(int(i[-1])).zfill(4)
                
        else:    
            splitStringBinary = np.binary_repr(int(i)).zfill(10)
            
        
        encData.append(splitStringBinary)

elif mode == 2:
    splitString = tw.wrap(inputText, 2)
    for i in splitString:
        firstVal= 0
        secondVal = 0
        totalVal = 0
        if len(i) == 2:
            for key, value in alNumTable.items():
                if value == i[0]:
                    firstVal = int(key) * 45

                if value == i[1]:
                    secondVal = int(key)
            totalVal = firstVal + secondVal
            splitStringBinary = np.binary_repr(totalVal).zfill(11)
        elif len(i) == 1:
            for key, value in alNumTable.items():
                if value == i[0]:
                    firstVal = int(key) * 45
                    secondVal = 0
            totalVal = firstVal + secondVal
            splitStringBinary = np.binary_repr(totalVal).zfill(11)
        
        encData.append(splitStringBinary)

elif mode == 4:
    #encodedIT = inputText.encode('iso-8859-1')
    for i in inputText:
        charHexed = i.encode('iso-8859-1').hex()
        charBinary = bin(int(charHexed, 16))[2:].zfill(8)
        encData.append(charBinary)

print(encData)
#Step 4: Break Up into 8-bit Codewords and Add Pad Bytes if Necessary
#bitString = mode + character count indicator + encoded data

bitString = np.binary_repr(mode) + cci + ''.join(map(str, encData))

#Determine the Required Number of Bits for this QR Code
#Total Number of Data Codewords for this Version and EC Level
tNDC = {"1": "19", "2": "34", "3": "55", "4": "80", "5": "108"}
totalNumOfBits = ''
for key, value in tNDC.items():
    if key == version:
        totalNumOfBits = int(value) * 8

terminator = '0000'
singleTerm = '0'
#Adding terminator if, required
if totalNumOfBits > len(bitString) and totalNumOfBits - len(bitString) > 3:
    bitString = ''.join((bitString, terminator))
elif totalNumOfBits > len(bitString) and totalNumOfBits - len(bitString) < 4:
    multiTerm = (totalNumOfBits - len(bitString))*singleTerm
    bitString = ''.join((bitString, multiTerm))

#make bitString divisable by 8
if len(bitString) % 8 != 0:
    mutliToEight = (8 - (len(bitString) % 8))*singleTerm
    bitString = ''.join((bitString, mutliToEight))

#Add Pad Bytes if the String is Still too Short
padBytes = ["11101100", "00010001"]
if len(bitString) != totalNumOfBits:
    padBytesCount = int((totalNumOfBits - len(bitString)) / 8)
    for i in range(padBytesCount):
        if i % 2 == 0:
            bitString += padBytes[0]
        elif i % 2 != 0:
            bitString += padBytes[1]

#build solomon-reed error correction algo OR build algo from scracth
#Error Correction Coding

#For error correction level L and version 1 to 5 we do not need more than 1 group, same applies to number of  blocks

#Error correction codewords per block v1 - 7, v2 - 10, v3, - 15, v4 - 20, v5 - 26


eccBlock = int(0)

if version == '1':
    eccBlock = 7
elif version == '2':
    eccBlock = 10
elif version == '3':
    eccBlock = 15
elif version == '4':
    eccBlock = 20
elif version == '5':
    eccBlock = 26

codeWords = tw.wrap(bitString, 8)

codeWordsBlock = []
for i in codeWords:
    codeWordsBlock.append(int(i, 2))

#using reedsolomon lib to get eccw
inputTextBytes = list(inputText.encode('iso-8859-1'))
rsc = reedsolo.RSCodec(eccBlock)
encodeITB = rsc.encode(inputTextBytes)
ecCodeWords = encodeITB[(len(inputText)):]

eccwDict=[]
for i in ecCodeWords:
    eccwDict.append(i)


#Structure Final Message
#As no interleaving is necessary, due to 1 group 1 block we'll be placing the eccCodeWords after codeWordsBlock

#convert finalMsg to 8bit binary
finalMsg = codeWordsBlock + eccwDict
fmBinary = ''
for i in finalMsg:
    fmBinary = ''.join((fmBinary, str(np.binary_repr(i)) ))


#adding remainder bits if necessary, based on version
reminderBits = int(0)
singleRB = '0'
if version != '1':
    reminderBits = 7 * singleRB
    fmBinary = ''.join((fmBinary, reminderBits))




#BUILDING THE QR CODE

#Allignment pattern center
columnsMatrix = {"2": "18", "3": "22", "4": "26", "5": "30"}
row = '6'
firstAlg = [row]
secondAlg = [row]
thirdAlg = []
fourthAlg = []
if version != '1':
    for key, value in columnsMatrix.items():
        if int(key) == int(version):
            firstAlg.append(row)
            secondAlg.append(value)
            thirdAlg.append(value)
            thirdAlg.append(row)
            fourthAlg.append(value)
            fourthAlg.append(value)

#size of the qr code

qrSize = (((int(version)-1)*4)+21)

codeArray = np.zeros((qrSize, qrSize)).astype(np.uint8)

positions = np.argwhere(codeArray == 0)
print(version)
for i, x in np.ndenumerate(codeArray):
    # orientation patterns
    #top-left
    if (i[0] == 0 and i[1] in range(0, 7)) or (i[0] == 6 and i[1] in range(0, 7) or (i[1] == 0 and i[0] in range(0, 7)) or (i[1] == 6 and i[0] in range(0, 7)) or (i[0] in range(2, 5) and i[1] in range(2, 5))):
        codeArray[i] = 1
    #top-right
    if (i[0] == 0 and i[1] in range((qrSize - 7), qrSize)) or (i[0] == 6 and i[1] in range((qrSize - 7), qrSize) or (i[1] == (qrSize - 7) and i[0] in range(0, 7)) or (i[1] == qrSize-1 and i[0] in range(0, 7)) or (i[0] in range(2, 5) and i[1] in range(qrSize - 5, qrSize - 2))):
        codeArray[i] = 1
    #bottom-left
    if (i[1] == 0 and i[0] in range((qrSize - 7), qrSize)) or (i[1] == 6 and i[0] in range((qrSize - 7), qrSize) or (i[0] == (qrSize - 7) and i[1] in range(0, 7)) or (i[0] == qrSize-1 and i[1] in range(0, 7)) or (i[1] in range(2, 5) and i[0] in range(qrSize - 5, qrSize - 2))):
        codeArray[i] = 1
    
    #no need to include sperators as the codeArray is prefilled with 0s

    #Allignment patterns for versions other than v1
    #firstAlg
    if int(version) > 1:
        if int(firstAlg[0]) - 2 not in range(0, 8) and int(firstAlg[1]) + 2 not in range (0, 8):
            if (i[0] == int(firstAlg[0]) - 2 and i[1] in range(int(firstAlg[1]) - 2, int(firstAlg[1]) + 2)) or (i[0] == int(firstAlg[0]) + 2 and i[1] in range(int(firstAlg[1]) - 2, int(firstAlg[1]) + 2)) or (i[1] == int(firstAlg[0]) - 2 and i[0] in range(int(firstAlg[1]) - 2, int(firstAlg[1]) + 2)) or (i[1] == int(firstAlg[0]) + 2 and i[0] in range(int(firstAlg[1]) - 2, int(firstAlg[1]) + 3)) or i[0] == int(firstAlg[0]) and i[1] == int(firstAlg[1]) :
                codeArray[i] = 1

        #secondAlg
        if int(secondAlg[0]) - 2 not in range (0, 8) and int(secondAlg[1]) + 2 not in range((qrSize - 8), qrSize):
            if (i[0] == int(secondAlg[0]) - 2 and i[1] in range(int(secondAlg[1]) - 2, int(secondAlg[1]) + 2)) or (i[0] == int(secondAlg[0]) + 2 and i[1] in range(int(secondAlg[1]) - 2, int(secondAlg[1]) + 2)) or (i[1] == int(secondAlg[0]) - 2 and i[0] in range(int(secondAlg[1]) - 2, int(secondAlg[1]) + 2)) or (i[1] == int(secondAlg[0]) + 2 and i[0] in range(int(secondAlg[1]) - 2, int(secondAlg[1]) + 3)) or i[0] == int(secondAlg[0]) and i[1] == int(secondAlg[1]) :
                codeArray[i] = 1

        #thirdAlg
        if int(thirdAlg[1]) - 2 not in range (0, 8) and int(thirdAlg[0]) + 2 not in range((qrSize - 8), qrSize):
            if (i[0] == int(thirdAlg[0]) - 2 and i[1] in range(int(thirdAlg[1]) - 2, int(thirdAlg[1]) + 2)) or (i[0] == int(thirdAlg[0]) + 2 and i[1] in range(int(thirdAlg[1]) - 2, int(thirdAlg[1]) + 2)) or (i[1] == int(thirdAlg[0]) - 2 and i[0] in range(int(thirdAlg[1]) - 2, int(thirdAlg[1]) + 2)) or (i[1] == int(thirdAlg[0]) + 2 and i[0] in range(int(thirdAlg[1]) - 2, int(thirdAlg[1]) + 3)) or i[0] == int(thirdAlg[0]) and i[1] == int(thirdAlg[1]) :
                codeArray[i] = 1

        #fourthAlg
        if (i[0] == int(fourthAlg[0]) - 2 and i[1] in range(int(fourthAlg[1]) - 2, int(fourthAlg[1]) + 2)) or (i[0] == int(fourthAlg[0]) + 2 and i[1] in range(int(fourthAlg[1]) - 2, int(fourthAlg[1]) + 2)) or (i[1] == int(fourthAlg[0]) - 2 and i[0] in range(int(fourthAlg[1]) - 2, int(fourthAlg[1]) + 2)) or (i[1] == int(fourthAlg[0]) + 2 and i[0] in range(int(fourthAlg[1]) - 2, int(fourthAlg[1]) + 3)) or i[0] == int(fourthAlg[0]) and i[1] == int(fourthAlg[1]) :
            codeArray[i] = 1
    
    
    # timing pattern
    if i[0] == 6 and i[1] in range(8, (qrSize - 8), 2) or i[1] == 6 and i[0] in range(8, (qrSize - 8), 2):
        codeArray[i] = 1

    #dark module  
    if (i[0] == ((4 * int(version)) + 9) and i[1] == 8):
        codeArray[i] = 1
    
    #Reserving format information area 
    if (i[0] == 8 and i[1] in range(0, 6)) or (i[0] == 8 and i[1] in range(7, 9)) or (i[0] == 8 and i[1] in range((qrSize - 8), qrSize)) or (i[1] == 8 and i[0] in range(0, 6)) or (i[1] == 8 and i[0] in range(7, 9)) or (i[1] == 8 and i[0] in range(((4 * int(version)) + 9) + 1, qrSize)):
        codeArray[i] = 0
    '''
    if (i[0] == 8 and i[1] in range(0, 9)) or (i[0] == 8 and i[1] in range((qrSize - 8), qrSize)) or (i[1] == 8 and i[0] in range(0, 9)) or (i[1] == 8 and i[0] in range(((4 * int(version)) + 9) + 1, qrSize)):
        codeArray[i] = 7
    '''
    #Reserve the Version Information Area - no need for that


print(codeArray)
#PLACING DATA BITS
positionsListUp = list()
positionsListDown = list()
positionsListOrdered = list()
positionsListReversed = list()
positionsListAll = list()
x = qrSize - 1
y = qrSize - 1
z = qrSize


upperList = list()
upperListToRemove = list()
downList = list()
downListToRemove = list()
positionsListExclude = list()
for i, v in np.ndenumerate(codeArray):
    if i[0] in range(0, 9) and i[1] in range(0,9):
        positionsListExclude.append(i)
    elif i[0] in range(0, 9) and i[1] in range(qrSize - 8, qrSize):
        positionsListExclude.append(i)
    elif i[0] in range(qrSize - 8, qrSize) and i[1] in range(0,9):
        positionsListExclude.append(i)
    elif i[0] == 6 and i[1] in range(8, (qrSize - 8)) or i[1] == 5 and i[0] in range(8, (qrSize - 8)):
        positionsListExclude.append(i)
    elif int(version) > 1 and i[0] in range(qrSize - 9, qrSize - 4) and i[1] in range(qrSize - 9, qrSize - 4):
        positionsListExclude.append(i)


while x > 0 or y > 0 or z > 0:
    for i, v in np.ndenumerate(codeArray):
        if i not in positionsListExclude:
            for x in range(z, -1, -1):
                if i[0] == x and i[1] == y:
                    positionsListUp.append(i)
                elif i[0] == x and i[1] == y - 1:
                    positionsListUp.append(i)
    

    for i in reversed(positionsListUp):
        positionsListReversed.append(i)
        upperListToRemove.append(i)

    upperList.append(list(upperListToRemove))

    upperListToRemove.clear()

    positionsListUp.clear()
    
    y -= 4

    if y < 0:
        break

a = 0
b = qrSize - 3
c = qrSize

while a > 0 or b > 0 or c > 0:
    for i, v in np.ndenumerate(codeArray):
        if i not in positionsListExclude:
            for a in range(-1, c, 1):
                if i[0] == a and i[1] == b:
                    positionsListDown.append(i)
                    downListToRemove.append(i)
                elif i[0] == a and i[1] == b - 1:
                    positionsListDown.append(i)
                    downListToRemove.append(i)

    downList.append(list(downListToRemove))
    downListToRemove.clear()

    b -= 4
    
    if b < 0:
        break


counter = 0
downListReversed = list()
downListReversedFinal = list()

while True:
    i = downList[counter]
    for j in i:
        j = list(j)
        if j[1] % 2 == 1:
            j[1] += 1
        elif j[1] % 2 == 0:
            j[1] -= 1
        i = tuple(j)
        downListReversed.append(i)
    
    downListReversedFinal.append(list(downListReversed))
    
    downListReversed.clear()

    counter += 1

    if counter == len(downList):
        break


#MECHANISM TO JOIN THE TWO LISTS IN PROPER ORDER

counter = 1
index = 0
positionsListAll = upperList

while True:
    positionsListAll.insert(counter, downListReversedFinal[index])
    index += 1
    counter += 2

    if counter > len(downListReversedFinal)*2:
        break

positonListFinal = list()
testList = list()
for i in positionsListAll:
    for j in i:
        k = tuple(j)
        positonListFinal.append(k)

print(fmBinary)
print(len(fmBinary))
print('xxxxxxxxx')
print(positonListFinal)
print(len(positonListFinal))

for c in range(0, len(fmBinary), 1):
    for i, v in np.ndenumerate(codeArray):
        if i == positonListFinal[c]:
            codeArray[i] = fmBinary[c]

print(codeArray)

#MASKING PART
#Applying mask nr.0 per formula (row + column) mod 2 == 0

def zeroMask():
    zeroMaskCA = codeArray.copy()
    for i, v in np.ndenumerate(zeroMaskCA):
        if i in positonListFinal:
            if (i[0] + i[1]) % 2 == 0:
                if v == 0:
                    zeroMaskCA[i] = 1
                elif v == 1:
                    zeroMaskCA[i] = 0
    return zeroMaskCA

#Applying mask nr.1 per formula (row) mod 2 == 0
def firstMask():
    firstMaskCA = codeArray.copy()
    for i, v in np.ndenumerate(firstMaskCA):
        if i in positonListFinal:
            if i[0] % 2 == 0:
                if v == 0:
                    firstMaskCA[i] = 1
                elif v == 1:
                    firstMaskCA[i] = 0
    return firstMaskCA

#Applying mask nr.2 per formula (column) mod 3 == 0
def secondMask():
    secondMaskCA = codeArray.copy()
    for i, v in np.ndenumerate(secondMaskCA):
        if i in positonListFinal:
            if i[1] % 3 == 0:
                if v == 0:
                    secondMaskCA[i] = 1
                elif v == 1:
                    secondMaskCA[i] = 0
    return secondMaskCA

#Applying mask nr.3 per formula (row + column) mod 3 == 0
def thirdMask():
    thirdMaskCA = codeArray.copy()
    for i, v in np.ndenumerate(thirdMaskCA):
        if i in positonListFinal:
            if (i[0] + i[1]) % 3 == 0:
                if v == 0:
                    thirdMaskCA[i] = 1
                elif v == 1:
                    thirdMaskCA[i] = 0
    return thirdMaskCA

#Applying mask nr.4 per formula ( floor(row / 2) + floor(column / 3) ) mod 2 == 0
def fourthMask():
    fourthMaskCA = codeArray.copy()
    for i, v in np.ndenumerate(fourthMaskCA):
        if i in positonListFinal:
            if (np.floor(i[0]/2) + np.floor(i[1]/2)) % 2 == 0.0:
                if v == 0:
                    fourthMaskCA[i] = 1
                elif v == 1:
                    fourthMaskCA[i] = 0
    return fourthMaskCA

#Applying mask nr.5 per formula ((row * column) mod 2) + ((row * column) mod 3) == 0
def fifthMask():
    fifthMaskCA = codeArray.copy()
    for i, v in np.ndenumerate(fifthMaskCA):
        if i in positonListFinal:
            if (((i[0] + i[1]) % 2)+((i[0] + i[1]) % 3)) == 0:
                if v == 0:
                    fifthMaskCA[i] = 1
                elif v == 1:
                    fifthMaskCA[i] = 0
    return fifthMaskCA

#Applying mask nr.6 per formula ( ((row * column) mod 2) + ((row * column) mod 3) ) mod 2 == 0
def sixthMask():
    sixthMaskCA = codeArray.copy()
    for i, v in np.ndenumerate(sixthMaskCA):
        if i in positonListFinal:
            if ((((i[0] + i[1]) % 2)+((i[0] + i[1]) % 3)) % 2) == 0:
                if v == 0:
                    sixthMaskCA[i] = 1
                elif v == 1:
                    sixthMaskCA[i] = 0
    return sixthMaskCA

#Applying mask nr.7 per formula 	( ((row + column) mod 2) + ((row * column) mod 3) ) mod 2 == 0
def seventhMask():
    seventhMaskCA = codeArray.copy()
    for i, v in np.ndenumerate(seventhMaskCA):
        if i in positonListFinal:
            if ((((i[0] + i[1]) % 2)+((i[0] + i[1]) % 3)) % 2) == 0:
                if v == 0:
                    seventhMaskCA[i] = 1
                elif v == 1:
                    seventhMaskCA[i] = 0
    return seventhMaskCA

#evalutaion - 1st condition
#For the first evaluation condition, check each row one-by-one. If there are five consecutive modules of the same color, add 3 to the penalty. If there are more modules of the same color after the first five, add 1 for each additional module of the same color.

def evaluation(evArr):
    penalty = 0
    countOcc = 0
    n = 0
    vertical = list()
    pVert = 0
    horizontal = list()
    pHor = 0
    horizontalModules = list()
    for i, v in np.ndenumerate(evArr):
        vertical.append(int(v))


    while True:

        if vertical[n] == vertical[(n+1)]:
            countOcc += 1
        else:
            countOcc = 0
        
        while countOcc >= 5:
            if countOcc == 5:
                pVert += 3
            elif countOcc > 5:
                pVert = 3 + (countOcc - 5)*1
            
            countOcc = 0

        n += 1

        if n == len(vertical)-1:
            break


    #For the first evaluation condition, check each column one-by-one. If there are five consecutive modules of the same color, add 3 to the penalty. If there are more modules of the same color after the first five, add 1 for each additional module of the same color

    for i, v in np.ndenumerate(evArr):
        horizontal.append((list(i)[1], list(i)[0]))

    for j in horizontal:
        for i, v in np.ndenumerate(evArr):
            if j == i:
                horizontalModules.append(int(v))

    m = 0
    while True:

        if horizontalModules[m] == horizontalModules[(m+1)]:
            countOcc += 1
        else:
            countOcc = 0
        
        while countOcc >= 5:
            if countOcc == 5:
                pHor += 3
            elif countOcc > 5:
                pHor = 3 + (countOcc - 5)*1
            
            countOcc = 0

        m += 1

        if m == len(horizontalModules)-1:
            break

    # Evaluation Condition #2 

    #creating list that would allow to find 2x2 blocks easier
    x = 0
    y = 0
    z = qrSize
    secondEv = list()
    while x > 0 or y > 0 or z > 0:
        for i, v in np.ndenumerate(evArr):
                for x in range(-1, z):
                    if i[0] == x and i[1] == y:
                        secondEv.append(int(v))
                    elif i[0] == x and i[1] == y + 1:
                        secondEv.append(int(v))
        
        y += 1

        if y > qrSize:
            break


    pSec = 0
    x = 0
    while True:
        if secondEv[x] == secondEv[x+1] == secondEv[x+2] == secondEv[x+3]:
            pSec += 3
        
        x += 2

        if (x + 3) == len(secondEv):
            break


    # Evaluation Condition #3 looking for patterns: 10111010000 OR 00001011101

    firstPattern = '10111010000'
    secondPattern = '00001011101'

    verticalToStr = ''.join(str(i) for i in vertical)
    horizontalToStr = ''.join(str(i) for i in horizontalModules)

    penaltyThirdEv= (verticalToStr.count(firstPattern) * 40) + (verticalToStr.count(secondPattern) * 40) + (horizontalToStr.count(firstPattern) * 40) + (horizontalToStr.count(secondPattern) * 40)

    # Evaluation Condition #4 dark to white patterns ratio

    totalList = list()
    for i, v in np.ndenumerate(evArr):
        totalList.append(str(v))

    totalListToStr = ''.join(totalList)


    totalListLen = len(totalListToStr)

    darkModules = totalListToStr.count('1')
    darkModulesPerc = (darkModules / totalListLen) * 100

    prevMultipleOfFive = (round(darkModulesPerc/5))*5

    nextMultipleOfFive = (int(np.ceil(darkModulesPerc/5)))*5

    pmofByTen = int((np.absolute(prevMultipleOfFive - 50)) / 5) 
    nmofByTen = int((np.absolute(nextMultipleOfFive - 50)) / 5)


    penaltyFourthEv = 0
    if pmofByTen < nmofByTen:
        penaltyFourthEv = pmofByTen * 10
    elif pmofByTen > nmofByTen:
        penaltyFourthEv = nmofByTen * 10

    penalty = pVert + pHor + pSec + penaltyThirdEv + penaltyFourthEv
    return penalty


zeroMask = zeroMask()

firstMask = firstMask()

secondMask = secondMask()

thirdMask = thirdMask()

fourthMask = fourthMask()

fifthMask =  fifthMask()

sixthMask = sixthMask()

seventhMask = seventhMask()



def selectingMask(zeroMask, firstMask, secondMask, thirdMask, fourthMask, fifthMask, sixthMask, seventhMask):

    evalList = list((evaluation(zeroMask), evaluation(firstMask), evaluation(secondMask), evaluation(thirdMask), evaluation(fourthMask), evaluation(fifthMask), evaluation(sixthMask), evaluation(seventhMask)))

    evalDict = {"zeroMask": evaluation(zeroMask), "firstMask": evaluation(firstMask), "secondMask": evaluation(secondMask), "thirdMask": evaluation(thirdMask), "fourthMask": evaluation(fourthMask), "fifthMask": evaluation(fifthMask), "sixthMask": evaluation(sixthMask), "seventhMask": evaluation(seventhMask)}

    minPenalty = min(evalList)

    for key, value in evalDict.items():
        if value == minPenalty:
            return key

selectedMask = selectingMask(zeroMask, firstMask, secondMask, thirdMask, fourthMask, fifthMask, sixthMask, seventhMask)


maskArray = ''
maskPatternVal = 0
if selectedMask == 'zeroMask':
    maskArray = zeroMask
    maskPatternVal = 0
elif selectedMask == 'firstMask':
    maskArray = zeroMask
    maskPatternVal = 1
elif selectedMask == 'secondMask':
    maskArray = zeroMask
    maskPatternVal = 2
elif selectedMask == 'thirdMask':
    maskArray = zeroMask
    maskPatternVal = 3
elif selectedMask == 'fourthMask':
    maskArray = zeroMask
    maskPatternVal = 4
elif selectedMask == 'fifthMask':
    maskArray = zeroMask
    maskPatternVal = 5
elif selectedMask == 'sixthMask':
    maskArray = zeroMask
    maskPatternVal = 6
elif selectedMask == 'seventhMask':
    maskArray = zeroMask
    maskPatternVal = 7



### The final step to creating a QR Code is to create the format and version strings, then place them in the correct locations in the QR code. 

#error correction level used is L so we go with 7 format information strings

formatInformationStrings = {"0": "111011111000100", "1": "111001011110011", "2": "111110110101010", "3": "111100010011101", "4": "110011000101111", "5": "110001100011000", "6": "110110001000001", "7": "110100101110110"}

selectedFIS = ''
for key, value in formatInformationStrings.items():
    if str(maskPatternVal) == key:
        selectedFIS = value


# Put the Format String into the QR Code

'''
for i, v in np.ndenumerate(maskArray):
     if (i[0] == 8 and i[1] in range(0, 9)) or (i[0] == 8 and i[1] in range((qrSize - 8), qrSize)) or (i[1] == 8 and i[0] in range(0, 9)) or (i[1] == 8 and i[0] in range(((4 * int(version)) + 9) + 1, qrSize)):
 '''
for i, v in np.ndenumerate(maskArray):
     if (i[0] == 8 and i[1] in range(0, 6)) or (i[0] == 8 and i[1] in range(7, 9)):
        maskArray[i] = 5
     elif (i[0] == 8 and i[1] in range((qrSize - 7), qrSize)):
        maskArray[i] = 6
     if (i[1] == 8 and i[0] in range(0, 6)) or (i[1] == 8 and i[0] in range(7, 9)):
        maskArray[i] = 7
     elif (i[1] == 8 and i[0] in range(((4 * int(version)) + 9) + 1, qrSize)):
        maskArray[i] = 8


firstFormatList = list()
secondFormatList = list()
secondReversedFormatList = list()
for i, v in np.ndenumerate(maskArray):
    if (i[0] == 8 and i[1] in range(0, 6)) or (i[0] == 8 and i[1] in range(7, 9)):
        firstFormatList.append(i)
    elif (i[0] == 8 and i[1] in range((qrSize - 7), qrSize)):
        firstFormatList.append(i)
    if (i[1] == 8 and i[0] in range(0, 6)) or (i[1] == 8 and i[0] in range(7, 9)):
        secondFormatList.append(i)
    elif (i[1] == 8 and i[0] in range(((4 * int(version)) + 9) + 1, qrSize)):
        secondFormatList.append(i)

for i in reversed(secondFormatList):
    secondReversedFormatList.append(i)

a = 0
while True:
    for i, v in np.ndenumerate(maskArray):
        if firstFormatList[a] == i:
            maskArray[i] = selectedFIS[a]

        if secondReversedFormatList[a] == i:
            maskArray[i] = selectedFIS[a]
    a+=1

    if a == len(firstFormatList):
        break


#Add the Quiet Zone

finalArray = np.pad(maskArray, (4,4), "constant", constant_values=(0,0))
print(finalArray)
print('XXXXXXXXXXXXXXX')

for i, v in np.ndenumerate(finalArray):

    if v == 0:
        finalArray[i] = 255
    elif v == 1:
        finalArray[i] = 0

print(finalArray)

#store qrCode as image in to a file
qrCode = Image.fromarray(finalArray, mode='L')

saveQrCode = qrCode.save('qr.png', 'png', quality=100)

qrCode = Image.open(r"qr.png")

#qrCode.thumbnail((99, 99), Image.Resampling.LANCZOS)

qrCode = ImageOps.contain(qrCode, (300, 300))

qrCode.save('qr2.png')

qrCode.show()

print(finalArray)
print(fmBinary)
print(encData)


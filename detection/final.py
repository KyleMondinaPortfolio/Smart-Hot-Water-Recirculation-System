# import necessary packages
import pandas as pd
import matplotlib.pyplot as plt
 
dfDryer = pd.read_csv('../data/dryer/dryer-1.xls')
# dfDryer = pd.read_csv('../data/dryer/dryer-2.xls')
# dfDryer = pd.read_csv('../data/dryer/dryer-3.xls')
# dfDryer = pd.read_csv('../data/dryer/dryer-4.xls')

dfShower1 = pd.read_csv('../data/shower/shower-1.xls')
dfShower2 = pd.read_csv('../data/shower/shower-2.xls')
dfShower3 = pd.read_csv('../data/shower/shower-3.xls')

dfMachine1 = pd.read_csv('../data/machine/washing-machine-1.xls')
dfMachine2 = pd.read_csv('../data/machine/washing-machine-2.xls')
dfMachine3 = pd.read_csv('../data/machine/washing-machine-3-imp.xls')
dfMachine4 = pd.read_csv('../data/machine/washing-machine-4.xls')
dfMachine5 = pd.read_csv('../data/machine/washing-machine-5.xls')

dfNot = pd.read_csv('../data/not-running.xls')



#taking first data x-axis valueof the column [0]
arrDryer = dfDryer.iloc[:,0]
arrShower1 = dfShower1.iloc[:,0]
arrShower2 = dfShower2.iloc[:,0]
arrShower3 = dfShower3.iloc[:,0]

arrMachine1 = dfMachine1.iloc[:,0]
arrMachine2 = dfMachine2.iloc[:,0]
arrMachine3 = dfMachine3.iloc[:,0]
arrMachine4 = dfMachine4.iloc[:,0]
arrMachine5 = dfMachine5.iloc[:,0]

arrNot = dfNot.iloc[:,0]

#taking second data y-axis valueof the column [1]
arrDryery = dfDryer.iloc[:,1]
arrShower1y = dfShower1.iloc[:,1]
arrShower2y = dfShower2.iloc[:,1]
arrShower3y = dfShower3.iloc[:,1]

arrMachine1y = dfMachine1.iloc[:,1]
arrMachine2y = dfMachine2.iloc[:,1]
arrMachine3y = dfMachine3.iloc[:,1]
arrMachine4y = dfMachine4.iloc[:,1]
arrMachine5y = dfMachine5.iloc[:,1]

arrNoty = dfNot.iloc[:,1]



# create a dataframe for x axis 
stockValuesArrayDryer = pd.DataFrame(
    {'values': arrDryer})

stockValuesArrayShower1 = pd.DataFrame(
    {'values': arrShower1})

stockValuesArrayShower2 = pd.DataFrame(
    {'values': arrShower2})

stockValuesArrayShower3 = pd.DataFrame(
    {'values': arrShower3})

stockValuesArrayMachine1 = pd.DataFrame(
    {'values': arrMachine1})

stockValuesArrayMachine2 = pd.DataFrame(
    {'values': arrMachine2})

stockValuesArrayMachine3 = pd.DataFrame(
    {'values': arrMachine3})

stockValuesArrayMachine4 = pd.DataFrame(
    {'values': arrMachine4})

stockValuesArrayMachine5 = pd.DataFrame(
    {'values': arrMachine5})


stockValuesArrayNot = pd.DataFrame(
    {'values': arrNot})

# create a dataframe for y axis 
stockValuesArrayDryery = pd.DataFrame(
    {'values': arrDryery})

stockValuesArrayShower1y = pd.DataFrame(
    {'values': arrShower1y})

stockValuesArrayShower2y = pd.DataFrame(
    {'values': arrShower2y})

stockValuesArrayShower3y = pd.DataFrame(
    {'values': arrShower3y})

stockValuesArrayMachine1y = pd.DataFrame(
    {'values': arrMachine1y})

stockValuesArrayMachine2y = pd.DataFrame(
    {'values': arrMachine2y})

stockValuesArrayMachine3y = pd.DataFrame(
    {'values': arrMachine3y})

stockValuesArrayMachine4y = pd.DataFrame(
    {'values': arrMachine4y})

stockValuesArrayMachine5y = pd.DataFrame(
    {'values': arrMachine5y})


stockValuesArrayNoty = pd.DataFrame(
    {'values': arrNoty})



# finding EMA for x
emaShower = stockValuesArrayShower3.ewm(alpha=0.8,adjust=True).mean()
# print(emaShower.max());
# emaMachine = stockValuesArrayMachine1.ewm(alpha=0.8,adjust=True).mean()
# print(emaMachine.max());

# finding EMA for y
emaShowery = stockValuesArrayShower3y.ewm(alpha=0.8,adjust=True).mean()
# print(emaShowery.max());
# emaMachiney = stockValuesArrayMachine1y.ewm(alpha=0.8,adjust=True).mean()
# print(emaMachiney.max());

#finding Max  for x
xAxis = 0;
yAxis = 0;

if (1.034 < emaShower.max()['values'] < 1.09) or (1.09 < emaShower.max()['values'] < 1.034):
    xAxis = 1;
else:
    xAxis = 0;

#finding Max  for y
if (0.2 < emaShowery.max()['values'] < 0.3) or (0.3 < emaShowery.max()['values'] < 0.2):
    yAxis = 1;
else:
    yAxis = 0;

if yAxis == xAxis == 1:
    print("hot water running!")
else:
    print("not the hot water :(")


# Comparison plot b/w stock values & EMA
# plt.plot(emaShower, label="Shower Values")
# plt.plot(emaMachine, label="Machine Values")

# plt.xlabel("Days")
# plt.ylabel("Vibration")
# plt.legend()
# plt.show()

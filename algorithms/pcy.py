import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import itertools
from collections import Counter
import csv
import random

def calculate_support(numRows,size,support_factors):
    support = support_factors[size] * numRows
    return support

def calculate_bucket(numRows):
     bucket_factor = 100  
     bucket_size = max(int(numRows**0.5), bucket_factor)
     return bucket_size  

# Define a hash function that maps a pair to a bucket
def hash_function(pair, bucket_size):
    # Convert the pair to a string and concatenate the elements
    pair_str = "".join(str(element) for element in pair)
    # Compute the hash value of the string using the built-in hash function
    # Map the hash value to a bucket using the modulo operator
    bucket = hash(pair_str) % bucket_size
    return bucket

def find_frequent_itemsets(transactions,size,support,bucket_size):
   
   #tests

  print(f"Support: {support}")
  print(f"Bucket size: {bucket_size}")
  print(f"Size: {size}")
  print(f"Transactions: {transactions}")
  
  
   #first pass
  freq=Counter()
  #test

  print(f"Initial Frequency Count: {freq}")

  buckets=[0]*bucket_size
  #test
  print(f"Initial Buckets: {buckets}")
  for row in transactions:
      for combo in itertools.combinations(row,size):
        freq[combo]+=1
        bucket=hash_function(combo,bucket_size)
        buckets[bucket]+=1

  print(f"Buckets after loop: {buckets}")
  bit_vector=[1 if count>=support else 0 for count in buckets]

  #test
  print(f"Bit Vector: {bit_vector}")

   #second pass
  frequent_itemsets={pair: count for pair, count in freq.items() if count>=support }

  #test
  print(f"Frequent Itemsets: {frequent_itemsets}")
  for combo in list(frequent_itemsets):
      bucket=hash_function(combo,bucket_size)
      if bit_vector[bucket]==0:
        del frequent_itemsets[combo]


  return frequent_itemsets

# Define the PCY algorithm

def PCY(data, column_name):
  # Extract the destinations column and split it by comma
  target_column = data[column_name].str.split(",").tolist()

  default_factors={2:0.04,3:0.1,4:0.1}
  # Calculate the number of rows in the dataset and calculate the support and bucket size
  all_frequent_itemsets = {}
  for size in range(2,5):
    numRows = len(data)
    support = calculate_support(numRows,size,default_factors)
    bucket_size = calculate_bucket(numRows)
    frequent_itemsets=find_frequent_itemsets(target_column,size,support,bucket_size)

    all_frequent_itemsets.update(frequent_itemsets)

  return all_frequent_itemsets

import numpy as np
import matplotlib.pyplot as plt
import json
from sklearn.cluster import KMeans

# Load the data from the JSON file alignment_data.json
with open('alignment_data.json', 'r') as f:
    data = json.load(f)

# Initialize the score matrix
num_sequences = len(data)
score_matrix = np.zeros((num_sequences, num_sequences))

# Fill the score matrix with the given data
for seq_index, alignments in data.items():
    seq_index = int(seq_index)
    for alignment in alignments:
        other_index = alignment["other_sequence_index"]
        score = alignment["score"]
        score_matrix[seq_index, other_index] = score
        score_matrix[other_index, seq_index] = score  # Assuming symmetry

# Perform KMeans clustering
k = 7  # Number of clusters, you can change this value
kmeans = KMeans(n_clusters=k, random_state=0).fit(score_matrix)
labels = kmeans.labels_

# Sort sequences based on cluster assignments
sorted_indices = np.argsort(labels)
sorted_score_matrix = score_matrix[sorted_indices, :][:, sorted_indices]

# Plot the upper triangular part of the sorted score matrix
plt.figure(figsize=(16, 14))
mask = np.triu(np.ones_like(sorted_score_matrix, dtype=bool))
plt.imshow(np.ma.masked_where(mask, sorted_score_matrix), cmap='viridis', interpolation='nearest')
plt.colorbar(label='Alignment Score')
plt.title('Alignment Score Matrix (Upper Triangular, Sorted by Clusters)')
plt.xlabel('Sequence Index')
plt.ylabel('Sequence Index')

# Adjust x and y ticks to reflect the original sequence indices
original_indices = np.array(list(data.keys()), dtype=int)
sorted_original_indices = original_indices[sorted_indices]
plt.xticks(ticks=np.arange(len(sorted_original_indices)), labels=sorted_original_indices, rotation=90)
plt.yticks(ticks=np.arange(len(sorted_original_indices)), labels=sorted_original_indices)

# Add labels to the top of the graph
plt.gca().xaxis.set_ticks_position('both')
plt.gca().tick_params(axis='x', which='both', bottom=True, top=True, labelbottom=True, labeltop=True)


plt.show()
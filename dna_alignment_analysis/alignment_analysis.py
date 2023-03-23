import itertools
import json
import os
from Bio import pairwise2
from tqdm import tqdm

# Function to read sequences from books.json
def read_sequences():
    with open('../books.json', 'r') as f:
        data = json.load(f)
    sequences = []
    if isinstance(data, list):
        if all(isinstance(item, dict) and 'sequence' in item for item in data):
            sequences = [item['sequence'] for item in data]
        elif all(isinstance(item, str) for item in data):
            sequences = data
        else:
            raise ValueError("Invalid format in books.json")
    else:
        raise ValueError("books.json should contain a list")
    return sequences

# Function to perform pairwise alignments and collect data
def collect_alignments(sequences):
    combination_data = {idx: [] for idx in range(len(sequences))}
    sequence_pairs = list(itertools.combinations(range(len(sequences)), 2))

    for idx1, idx2 in tqdm(sequence_pairs, desc="Performing sequence alignments"):
        seq1 = sequences[idx1]
        seq2 = sequences[idx2]

        # Create an alignment
        alignments = pairwise2.align.globalms(seq1, seq2, 2, -1, -0.5, -0.1)
        best_alignment = alignments[0]

        seqA = best_alignment.seqA
        seqB = best_alignment.seqB

        # Generate alignment symbol line
        alignment_str = ''
        for a, b in zip(seqA, seqB):
            if a == b and a != '-':
                alignment_str += '|'
            else:
                alignment_str += ' '

        # Fix alignment label spacing
        label_seq1 = f"Sequence {idx1}:"
        label_seq2 = f"Sequence {idx2}:"
        label_length = max(len(label_seq1), len(label_seq2))

        # Adjust labels to have the same length
        label_seq1 = label_seq1.ljust(label_length)
        label_seq2 = label_seq2.ljust(label_length)

        alignment_info = {
            'other_sequence_index': idx2,
            'score': best_alignment.score,
            'alignment': {
                'seq1_label': label_seq1,
                'seq1': seqA,
                'alignment_str': alignment_str,
                'seq2_label': label_seq2,
                'seq2': seqB
            }
        }

        # Append alignment info to both sequences
        combination_data[idx1].append(alignment_info)
        combination_data[idx2].append({
            'other_sequence_index': idx1,
            'score': best_alignment.score,
            'alignment': {
                'seq1_label': label_seq2,
                'seq1': seqB,
                'alignment_str': alignment_str,
                'seq2_label': label_seq1,
                'seq2': seqA
            }
        })

    return combination_data

# Function to write all alignments for each book into one .md file
def write_markdown_files(combination_data, output_dir):

    for idx, alignments in combination_data.items():
        md_content = f"# Alignments for Sequence {idx}\n\n"
        for alignment in alignments:
            other_idx = alignment['other_sequence_index']
            score = alignment['score']
            seq1_label = alignment['alignment']['seq1_label']
            seq1 = alignment['alignment']['seq1']
            alignment_str = alignment['alignment']['alignment_str']
            seq2_label = alignment['alignment']['seq2_label']
            seq2 = alignment['alignment']['seq2']

            md_content += f"## Alignment with Sequence {other_idx}\n\n"
            md_content += f"**Score:** {score}\n\n"
            md_content += "```\n"
            md_content += f"{seq1_label} {seq1}\n"
            md_content += f"{' ' * len(seq1_label)} {alignment_str}\n"
            md_content += f"{seq2_label} {seq2}\n"
            md_content += "```\n\n"

        output_file = os.path.join(output_dir, f'sequence_{idx}.md')
        with open(output_file, 'w') as f:
            f.write(md_content)
        print(f"Markdown file saved to {output_file}")

# Main Function
def main():
    sequences = read_sequences()

    # Prepare output directory
    output_dir = os.path.join('alignment_analysis')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Collect alignment data
    combination_data = collect_alignments(sequences)
    print(f"Collected combination data for {len(combination_data)} sequences.")

    # Write all alignments for each book into one Markdown file
    write_markdown_files(combination_data, output_dir)

    # Write all alignments for each book into one JSON file
    with open('alignment_data.json', 'w') as f:
        json.dump(combination_data, f, indent=2)

if __name__ == "__main__":
    main()

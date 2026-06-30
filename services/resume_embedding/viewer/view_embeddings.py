"""
Embedding Viewer — Inspect and explore .npy embedding outputs.

Usage:
    python viewer/view_embeddings.py outputs/sample_50/

Features:
    - Summary statistics (shape, dtype, norms)
    - Per-candidate embedding preview
    - Top-N most similar candidate pairs
    - Search: find candidates most similar to a given candidate ID
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def load_output(output_dir: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    """Load embeddings, candidate IDs, and metadata from an output directory."""
    emb_path = output_dir / "embeddings.npy"
    ids_path = output_dir / "candidate_ids.npy"
    meta_path = output_dir / "metadata.json"

    if not emb_path.exists():
        print(f"ERROR: embeddings.npy not found in {output_dir}")
        sys.exit(1)
    if not ids_path.exists():
        print(f"ERROR: candidate_ids.npy not found in {output_dir}")
        sys.exit(1)

    embeddings = np.load(emb_path)
    candidate_ids = np.load(ids_path, allow_pickle=True)
    metadata = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    return embeddings, candidate_ids, metadata


def print_summary(embeddings: np.ndarray, candidate_ids: np.ndarray, metadata: dict) -> None:
    """Print a summary of the embedding output."""
    norms = np.linalg.norm(embeddings, axis=1)

    print("=" * 60)
    print("EMBEDDING OUTPUT SUMMARY")
    print("=" * 60)
    print(f"  Candidates:     {len(candidate_ids)}")
    print(f"  Dimensions:     {embeddings.shape[1]}")
    print(f"  Shape:          {embeddings.shape}")
    print(f"  Dtype:          {embeddings.dtype}")
    print(f"  File size:      {embeddings.nbytes / 1024:.1f} KB")
    print()
    print(f"  L2 norms:       min={norms.min():.6f}  max={norms.max():.6f}")
    print(f"  All unit-norm:  {np.allclose(norms, 1.0, atol=1e-5)}")
    print()
    print(f"  Value range:    [{embeddings.min():.6f}, {embeddings.max():.6f}]")
    print(f"  Mean:           {embeddings.mean():.6f}")
    print(f"  Std:            {embeddings.std():.6f}")

    if metadata:
        print()
        print("  --- Metadata ---")
        print(f"  Model:          {metadata.get('model', 'N/A')}")
        print(f"  Device:         {metadata.get('device', 'N/A')}")
        print(f"  Timestamp:      {metadata.get('timestamp', 'N/A')}")
        print(f"  Input file:     {metadata.get('input_file', 'N/A')}")

    print()
    print(f"  First 5 IDs:    {', '.join(candidate_ids[:5])}")
    print(f"  Last 5 IDs:     {', '.join(candidate_ids[-5:])}")
    print("=" * 60)


def show_candidate(
    candidate_id: str,
    embeddings: np.ndarray,
    candidate_ids: np.ndarray,
) -> None:
    """Show the embedding vector for a specific candidate."""
    matches = np.where(candidate_ids == candidate_id)[0]
    if len(matches) == 0:
        print(f"ERROR: '{candidate_id}' not found. Available: {candidate_ids[0]} ... {candidate_ids[-1]}")
        return

    idx = matches[0]
    vec = embeddings[idx]
    norm = np.linalg.norm(vec)

    print(f"\n--- {candidate_id} (index {idx}) ---")
    print(f"  L2 norm:  {norm:.8f}")
    print(f"  Min/Max:  [{vec.min():.6f}, {vec.max():.6f}]")
    print(f"  Mean:     {vec.mean():.6f}")
    print(f"  Std:      {vec.std():.6f}")
    print("\n  First 20 values:")
    print(f"  {vec[:20]}")
    print("\n  Last 10 values:")
    print(f"  {vec[-10:]}")


def find_similar(
    candidate_id: str,
    embeddings: np.ndarray,
    candidate_ids: np.ndarray,
    top_n: int = 10,
) -> None:
    """Find the top-N most similar candidates to a given candidate."""
    matches = np.where(candidate_ids == candidate_id)[0]
    if len(matches) == 0:
        print(f"ERROR: '{candidate_id}' not found.")
        return

    idx = matches[0]
    query = embeddings[idx]

    # Cosine similarity (vectors are L2-normalized, so dot product = cosine sim)
    scores = embeddings @ query
    ranked = np.argsort(scores)[::-1]

    print(f"\n--- Top {top_n} similar to {candidate_id} ---")
    print(f"{'Rank':<6} {'Candidate ID':<18} {'Similarity':<12}")
    print("-" * 36)

    count = 0
    for r in ranked:
        if candidate_ids[r] == candidate_id:
            continue  # skip self
        count += 1
        print(f"{count:<6} {candidate_ids[r]:<18} {scores[r]:.6f}")
        if count >= top_n:
            break


def top_pairs(
    embeddings: np.ndarray,
    candidate_ids: np.ndarray,
    top_n: int = 10,
) -> None:
    """Find the top-N most similar candidate pairs across the entire dataset."""
    # Compute full similarity matrix
    sim_matrix = embeddings @ embeddings.T

    # Zero out the diagonal (self-similarity) and lower triangle (duplicates)
    np.fill_diagonal(sim_matrix, -1)
    sim_matrix = np.triu(sim_matrix)

    # Find top pairs
    flat_indices = np.argsort(sim_matrix.ravel())[::-1][:top_n]
    rows, cols = np.unravel_index(flat_indices, sim_matrix.shape)

    print(f"\n--- Top {top_n} Most Similar Pairs ---")
    print(f"{'Rank':<6} {'Candidate A':<18} {'Candidate B':<18} {'Similarity':<12}")
    print("-" * 54)

    for rank, (r, c) in enumerate(zip(rows, cols, strict=True), 1):
        print(f"{rank:<6} {candidate_ids[r]:<18} {candidate_ids[c]:<18} {sim_matrix[r, c]:.6f}")


def compare_candidates(
    id_a: str,
    id_b: str,
    embeddings: np.ndarray,
    candidate_ids: np.ndarray,
) -> None:
    """Compare two specific candidates side by side."""
    idx_a = np.where(candidate_ids == id_a)[0]
    idx_b = np.where(candidate_ids == id_b)[0]

    if len(idx_a) == 0:
        print(f"ERROR: '{id_a}' not found.")
        return
    if len(idx_b) == 0:
        print(f"ERROR: '{id_b}' not found.")
        return

    vec_a = embeddings[idx_a[0]]
    vec_b = embeddings[idx_b[0]]
    similarity = float(np.dot(vec_a, vec_b))
    diff = vec_a - vec_b

    print(f"\n--- Comparing {id_a} vs {id_b} ---")
    print(f"  Cosine similarity:  {similarity:.6f}")
    print(f"  Euclidean distance: {np.linalg.norm(diff):.6f}")
    print(f"  Max abs diff:       {np.abs(diff).max():.6f}")
    print(f"  Mean abs diff:      {np.abs(diff).mean():.6f}")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect and explore .npy embedding outputs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python viewer/view_embeddings.py outputs/sample_50/\n"
            "  python viewer/view_embeddings.py outputs/sample_50/ --show CAND_0000001\n"
            "  python viewer/view_embeddings.py outputs/sample_50/ --similar CAND_0000001 --top 5\n"
            "  python viewer/view_embeddings.py outputs/sample_50/ --pairs --top 10\n"
            "  python viewer/view_embeddings.py outputs/sample_50/ --compare CAND_0000001 CAND_0000002\n"
        ),
    )
    parser.add_argument("output_dir", type=str, help="Path to the output directory containing .npy files.")
    parser.add_argument("--show", type=str, metavar="ID", help="Show embedding details for a specific candidate ID.")
    parser.add_argument("--similar", type=str, metavar="ID", help="Find candidates most similar to this ID.")
    parser.add_argument("--pairs", action="store_true", help="Show the top most similar candidate pairs.")
    parser.add_argument("--compare", nargs=2, metavar=("ID_A", "ID_B"), help="Compare two candidates side by side.")
    parser.add_argument("--top", type=int, default=10, help="Number of results to show (default: 10).")

    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    embeddings, candidate_ids, metadata = load_output(output_dir)

    # Always show summary
    print_summary(embeddings, candidate_ids, metadata)

    if args.show:
        show_candidate(args.show, embeddings, candidate_ids)

    if args.similar:
        find_similar(args.similar, embeddings, candidate_ids, top_n=args.top)

    if args.pairs:
        top_pairs(embeddings, candidate_ids, top_n=args.top)

    if args.compare:
        compare_candidates(args.compare[0], args.compare[1], embeddings, candidate_ids)

    # If no specific action, show pairs by default
    if not args.show and not args.similar and not args.pairs and not args.compare:
        top_pairs(embeddings, candidate_ids, top_n=args.top)


if __name__ == "__main__":
    main()

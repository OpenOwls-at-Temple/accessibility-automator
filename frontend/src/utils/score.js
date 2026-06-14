// Map a 0-100 accessibility score to a Panorama-style colour band
// (red / yellow / green; see domain-knowledge.md).
export function scoreBand(score) {
  if (score == null) return "muted";
  if (score >= 67) return "green";
  if (score >= 34) return "yellow";
  return "red";
}

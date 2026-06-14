import { describe, expect, it } from "vitest";
import { scoreBand } from "../src/utils/score.js";

describe("scoreBand", () => {
  it("maps scores to Panorama colour bands", () => {
    expect(scoreBand(100)).toBe("green");
    expect(scoreBand(67)).toBe("green");
    expect(scoreBand(50)).toBe("yellow");
    expect(scoreBand(34)).toBe("yellow");
    expect(scoreBand(10)).toBe("red");
  });

  it("treats a missing score as muted", () => {
    expect(scoreBand(null)).toBe("muted");
    expect(scoreBand(undefined)).toBe("muted");
  });
});

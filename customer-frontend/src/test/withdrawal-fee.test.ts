import { describe, expect, it } from "vitest";
import { addMoney, percentageFee } from "../utils/money";

describe("процентная комиссия вывода", () => {
  it.each([
    ["20", "2.000000", "22.000000"],
    ["50", "5.000000", "55.000000"],
    ["100", "10.000000", "110.000000"],
    ["20.000004", "2.000000", "22.000004"],
    ["20.000005", "2.000001", "22.000006"],
    ["9223372036854.775807", "922337203685.477581", "10145709240540.253388"],
  ])("для %s считает 10%% и общую сумму точно", (amount, fee, total) => {
    expect(percentageFee(amount, 10)).toBe(fee);
    expect(addMoney(amount, percentageFee(amount, 10))).toBe(total);
  });

  it("не допускает отрицательные суммы и некорректный процент", () => {
    expect(() => percentageFee("-1", 10)).toThrow();
    expect(() => percentageFee("50", -1)).toThrow();
    expect(() => percentageFee("50", 101)).toThrow();
    expect(() => percentageFee("50", 10.5)).toThrow();
  });
});

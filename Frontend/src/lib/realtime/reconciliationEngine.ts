export class ReconciliationEngine {
  private seenEventIds = new Set<string>();
  
  public isDuplicate(eventId: string): boolean {
    if (this.seenEventIds.has(eventId)) return true;
    this.seenEventIds.add(eventId);
    if (this.seenEventIds.size > 1000) {
      // Memory cleanup, keep only recent ones. In a real system, we'd use a rolling array.
      const arr = Array.from(this.seenEventIds).slice(-500);
      this.seenEventIds = new Set(arr);
    }
    return false;
  }
}
export const reconciliationEngine = new ReconciliationEngine();

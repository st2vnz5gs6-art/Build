"use client";

/**
 * No accounts in Phase 1. A "member" is a display name pinned to a random id
 * stashed in localStorage, per group. Trivially spoofable — that's an
 * accepted tradeoff for a zero-friction, no-money product.
 */

export type LocalMember = {
  memberId: string;
  name: string;
  initials: string;
};

function storageKey(groupCode: string) {
  return `coupon:member:${groupCode.toUpperCase()}`;
}

export function getLocalMember(groupCode: string): LocalMember | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(storageKey(groupCode));
    return raw ? (JSON.parse(raw) as LocalMember) : null;
  } catch {
    return null;
  }
}

export function setLocalMember(groupCode: string, member: LocalMember) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(storageKey(groupCode), JSON.stringify(member));
}

const AGE_GATE_KEY = "coupon:age-confirmed";

export function hasConfirmedAge(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(AGE_GATE_KEY) === "1";
}

export function confirmAge() {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AGE_GATE_KEY, "1");
}

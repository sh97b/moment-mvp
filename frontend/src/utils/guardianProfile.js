const PROFILE_STORAGE_KEY = 'moment.guardian-profiles'
const ACTIVE_PROFILE_STORAGE_KEY = 'moment.active-guardian-profile'

export function normalizeRegistrationCode(value = '') {
  return String(value).trim().replace(/[^A-Za-z0-9]/g, '').toUpperCase()
}

export function isValidRegistrationCode(value = '') {
  return /^[A-Z0-9]{5}$/.test(normalizeRegistrationCode(value))
}

export function generateUniqueCode(existingCodes = []) {
  const normalized = new Set((existingCodes ?? []).map((code) => normalizeRegistrationCode(code)))
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

  let candidate = ''
  do {
    candidate = Array.from({ length: 5 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join('')
  } while (normalized.has(candidate) || candidate.length !== 5)

  normalized.add(candidate)
  return candidate
}

export function readGuardianProfiles() {
  if (typeof window === 'undefined') return []

  try {
    const raw = window.localStorage.getItem(PROFILE_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function writeGuardianProfiles(profiles = []) {
  if (typeof window === 'undefined') return profiles

  window.localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profiles))
  return profiles
}

export function normalizeGuardianName(value = '') {
  const name = String(value ?? '').trim()
  return name || '보호 대상자'
}

export function saveActiveGuardianProfile(profile) {
  if (typeof window === 'undefined') return null

  const normalized = profile && typeof profile === 'object' ? { ...profile } : null
  if (!normalized) {
    window.localStorage.removeItem(ACTIVE_PROFILE_STORAGE_KEY)
    return null
  }

  const safeProfile = {
    code: normalizeRegistrationCode(normalized.code),
    name: normalizeGuardianName(normalized.name),
    createdAt: normalized.createdAt ?? new Date().toISOString(),
  }

  window.localStorage.setItem(ACTIVE_PROFILE_STORAGE_KEY, JSON.stringify(safeProfile))
  return safeProfile
}

export function readActiveGuardianProfile() {
  if (typeof window === 'undefined') return null

  try {
    const raw = window.localStorage.getItem(ACTIVE_PROFILE_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : null
    if (!parsed || !parsed.code || !parsed.name) return null
    return {
      code: normalizeRegistrationCode(parsed.code),
      name: normalizeGuardianName(parsed.name),
      createdAt: parsed.createdAt ?? new Date().toISOString(),
    }
  } catch {
    return null
  }
}

export function createGuardianProfile(name = '') {
  const profiles = readGuardianProfiles()
  const normalizedName = normalizeGuardianName(name)
  const suggested = generateUniqueCode(profiles.map((profile) => profile.code))
  const created = {
    code: suggested,
    name: normalizedName,
    createdAt: new Date().toISOString(),
  }

  writeGuardianProfiles([...profiles, created])
  return saveActiveGuardianProfile(created)
}

export function findGuardianProfileByCode(code = '') {
  const normalizedCode = normalizeRegistrationCode(code)
  if (!normalizedCode) return null

  const profiles = readGuardianProfiles()
  return profiles.find((profile) => normalizeRegistrationCode(profile.code) === normalizedCode) ?? null
}

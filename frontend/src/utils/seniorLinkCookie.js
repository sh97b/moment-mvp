const COOKIE_NAME = 'moment_senior_link'
const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
const CODE_CHARACTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
const CONNECTION_CODE_LENGTH = 5

export const MASTER_CONNECTION_CODE = '12345'

export function createSeniorConnectionCode() {
  const randomValues = new Uint32Array(CONNECTION_CODE_LENGTH)
  window.crypto.getRandomValues(randomValues)

  return Array.from(
    randomValues,
    (value) => CODE_CHARACTERS[value % CODE_CHARACTERS.length],
  ).join('')
}

export function saveSeniorLinkCookie(personName, code) {
  const value = encodeURIComponent(JSON.stringify({ personName, code }))
  document.cookie = `${COOKIE_NAME}=${value}; Path=/; Max-Age=${COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`
}

export function readSeniorLinkCookie() {
  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${COOKIE_NAME}=`))

  if (!cookie) return null

  try {
    const value = JSON.parse(decodeURIComponent(cookie.slice(COOKIE_NAME.length + 1)))
    if (
      typeof value.personName !== 'string' ||
      !value.personName.trim() ||
      typeof value.code !== 'string' ||
      value.code.length !== CONNECTION_CODE_LENGTH
    ) {
      return null
    }

    return { personName: value.personName.trim(), code: value.code.toUpperCase() }
  } catch {
    return null
  }
}

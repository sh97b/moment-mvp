import test from 'node:test'
import assert from 'node:assert/strict'
import {
  generateUniqueCode,
  isValidRegistrationCode,
  normalizeRegistrationCode,
} from './guardianProfile.js'

test('generateUniqueCode creates a 5-character uppercase code that avoids duplicates', () => {
  const first = generateUniqueCode(['AB123'])
  assert.equal(first.length, 5)
  assert.match(first, /^[A-Z0-9]{5}$/)
  assert.notEqual(first, 'AB123')

  const second = generateUniqueCode([first])
  assert.equal(second.length, 5)
  assert.match(second, /^[A-Z0-9]{5}$/)
  assert.notEqual(first, second)
})

test('normalizeRegistrationCode trims and uppercases the user input', () => {
  assert.equal(normalizeRegistrationCode(' ab-12 3 '), 'AB123')
  assert.equal(normalizeRegistrationCode('xyz12'), 'XYZ12')
})

test('isValidRegistrationCode accepts only 5-character alphanumeric codes', () => {
  assert.equal(isValidRegistrationCode('AB123'), true)
  assert.equal(isValidRegistrationCode('AB12'), false)
  assert.equal(isValidRegistrationCode('AB-12'), false)
})

import axios from 'axios'

/**
 * Defines the base url and headers for validate http calls
 */

const Validate = axios.create({
  baseURL: '/service/validate',
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept',
    'Access-Control-Allow-Methods': 'GET, POST, DELETE, PUT'
  }
})

const createErrorPayload = err => {
  return {
    valid: false,
    data: err.response.data.error_key
  }
}

export default {
  cpr (cpr, org) {
    const payload = {
      'cpr_no': cpr,
      'org': {
        'uuid': org[0]
      }
    }
    return Validate
      .post('/cpr/', payload).then(result => {
        return true
      }, err => {
        return createErrorPayload(err)
      })
  },

  orgUnit (orgUnit, validity) {
    const payload = {
      'org_unit': {
        'uuid': orgUnit
      },
      'validity': validity
    }
    return Validate
      .post('/org-unit/', payload).then(result => {
        return true
      }, err => {
        return createErrorPayload(err)
      })
  }
}
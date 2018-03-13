import { Service } from './HttpCommon'
import { EventBus } from '../EventBus'

export default {

  /**
   * Get a list of all employees
   * @returns {Array} List of all employees
   */
  getAll (orgUuid) {
    return Service.get(`/o/${orgUuid}/e/`)
      .then(response => {
        return response.data.items
      })
      .catch(error => {
        console.log(error.response)
      })
  },

  /**
   * Get an employee
   * @param {String} uuid - uuid for employee
   * @returns {Object} employee object
   */
  get (uuid) {
    return Service.get(`/e/${uuid}/`)
      .then(response => {
        EventBus.$emit('organisation-changed', response.data.org)
        return response.data
      })
      .catch(error => {
        console.log(error.response)
      })
  },

  history (uuid) {
    return Service.get(`/e/${uuid}/history/`)
      .then(response => {
        return response.data
      })
  },

  /**
   * Get engagement details for employee
   * @param {String} uuid - employee uuid
   * @see getDetail
   */
  getEngagementDetails (uuid, validity) {
    return this.getDetail(uuid, 'engagement', validity)
  },

  /**
   * Get role details for employee
   * @param {String} uuid - Employee uuid
   * @see getDetail
   */
  getRoleDetails (uuid, validity) {
    return this.getDetail(uuid, 'role', validity)
  },

  /**
   * Get IT details for employee
   * @param {String} uuid - Employee uuid
   * @see getDetail
   */
  getItDetails (uuid, validity) {
    return this.getDetail(uuid, 'it', validity)
  },

  /**
   * Get association details for employee
   * @param {String} uuid - Employee uuid
   * @see getDetail
   */
  getAssociationDetails (uuid, validity) {
    return this.getDetail(uuid, 'association', validity)
  },

  /**
   * Get leave details for employee
   * @param {String} uuid - Employee uuid
   * @see getDetail
   */
  getLeaveDetails (uuid, validity) {
    return this.getDetail(uuid, 'leave', validity)
  },

  /**
   * Base call for getting details.
   * @param {String} uuid - employee uuid
   * @param {String} detail - Name of the detail
   * @returns {Array} A list of options for the detail
   */
  getDetail (uuid, detail, validity) {
    validity = validity || 'present'
    return Service.get(`/e/${uuid}/details/${detail}?validity=${validity}`)
      .then(response => {
        return response.data
      })
      .catch(error => {
        console.log(error.response)
      })
  },

  /**
   * Get a list of available details
   * @param {String} uuid - employee uuid
   * @returns {Object} A list of available tabs
   */
  getDetailList (uuid) {
    return Service.get(`e/${uuid}/details/`)
      .then(response => {
        return response.data
      })
      .catch(error => {
        console.log(error.response)
      })
  },

  /**
   * Create a new employee
   * @param {String} uuid - employee uuid
   * @param {Array} create - A list of elements to create
   * @returns {Object} employee uuid
   */
  createEntry (uuid, create) {
    return Service.post(`/e/${uuid}/create`, create)
      .then(response => {
        EventBus.$emit('employee-changed', response.data)
        return response.data
      })
      .catch(error => {
        console.log(error.response)
      })
  },

  create (uuid, create) {
    return this.createEntry(uuid, create)
      .then(response => {
        EventBus.$emit('employee-create', response)
      })
  },

  leave (uuid, leave) {
    return this.createEntry(uuid, leave)
      .then(response => {
        EventBus.$emit('employee-leave', response)
      })
  },

  /**
   * Move an employee
   * @param {String} uuid - employee uuid
   * @param {Array} edit - A list of elements to edit
   * @returns {Object} employeee uuid
   */
  edit (uuid, edit) {
    return Service.post(`/e/${uuid}/edit`, edit)
      .then(response => {
        EventBus.$emit('employee-changed', response.data)
        return response.data
      })
      .catch(error => {
        console.log(error.response)
      })
  },

  move (uuid, move) {
    return this.edit(uuid, move)
      .then(response => {
        EventBus.$emit('employee-move', response)
      })
  },

  /**
   * End an employee
   * @param {String} uuid - employee uuid
   * @param {Object} end - Object containing the end date
   * @returns {Object} employee uuid
   */
  terminate (uuid, end) {
    return Service.post(`/e/${uuid}/terminate`, end)
      .then(response => {
        EventBus.$emit('employee-changed', response.data)
        EventBus.$emit('employee-terminate', response.data)
        return response.data
      })
      .catch(error => {
        console.log(error.response)
      })
  }
}

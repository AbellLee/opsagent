import { defineStore } from 'pinia'

export const useToolStore = defineStore('tool', {
  state: () => ({
    tools: [],
    approvals: []
  }),
  
  actions: {
    setTools(tools) {
      this.tools = tools
    },
    
    setApprovals(approvals) {
      this.approvals = approvals
    },
    
    updateApprovalStatus(approvalId, status) {
      const approval = this.approvals.find(a => a.id === approvalId)
      if (approval) {
        approval.status = status
      }
    }
  }
})
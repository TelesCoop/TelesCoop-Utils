import { defineStore } from "pinia"
// import { Alert } from "~/composables/types"
// import { generateRandomId } from "~/composables/utils"

const SUCCESS_ALERT_DURATION = 5000 // ms
const ERROR_ALERT_DURATION = 15000 // ms

const generateRandomId = () => Math.random().toString(36).slice(2, 10)
export type Alert = {
    id?: string
    title: string
    text?: string
    type?: string
}


export const useAlertStore = defineStore("alerts", {
    state: () => {
        return { alerts: <{ [key: string]: Alert }>{} }
    },
    actions: {
        alert(title: string, text = "", type = "success") {
            if (process.server) {
                return
            }
            const alertId = generateRandomId()
            this.alerts[alertId] = {
                text: text.substring(0, 300),
                title,
                type,
                id: alertId,
            }
            const duration =
                type === "success" ? SUCCESS_ALERT_DURATION : ERROR_ALERT_DURATION
            setTimeout(() => this.removeAlert(alertId), duration)
        },
        removeAlert(alertId: string) {
            delete this.alerts[alertId]
        },
    },
    getters: {
        getAlerts: (state): Alert[] => {
            return Object.values(state.alerts).reverse()
        },
    },
})
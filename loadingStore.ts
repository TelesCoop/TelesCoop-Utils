import { defineStore } from "pinia"

type LoadingStoreState = {
    statePerKey: { [key: string]: "loading" | "done" | "error" }
    visibleKey: string
    message: string
}

export const useLoadingStore = defineStore("loading", {
    state: () =>
        <LoadingStoreState>{
            statePerKey: {},
            visibleKey: "",
            message: "",
        },
    actions: {
        markLoading(key: string, message: string | boolean = false) {
            this.statePerKey[key] = "loading"
            this.visibleKey = !!message ? key : ""
            this.message = typeof message === "string" ? message : ""
        },
        markDone(key: string) {
            this.statePerKey[key] = "done"
        },
        markError(key: string) {
            this.statePerKey[key] = "error"
        },
    },
    getters: {
        isLoading: (state) => {
            return (key: string) => {
                return state.statePerKey[key] === "loading"
            }
        },
        showLoadingOverlay: (state) =>
            state.visibleKey && state.statePerKey[state.visibleKey] === "loading",
    },
})
import { useLoadingStore } from "~/stores/loadingStore"
import { Alert } from "~/composables/types"
import { useAlertStore } from "~/stores/alertStore"

let base_url = ""
type MyHeaders = { [key: string]: string }

// local
if (process.env.NODE_ENV !== "production") {
    base_url = "http://localhost:8000"
} else {
    // production server
    if (process.server) {
        const port = process.env.API_PORT || "8000"
        // server-side rendering
        base_url = `http://localhost:${port}`
    }
}

const makeLoadingKey = (path: string) => {
    // camel-case the path : auth/login -> authLogin
    if (path.endsWith("/")) {
        path = path.slice(0, -1)
    }
    if (path.startsWith("/")) {
        path = path.slice(1)
    }
    let words = path.split("/")
    words = words.filter((word) => !/^\d+$/.test(word))
    for (const [ix, word] of Object.entries(words.slice(1))) {
        const newWord = word[0].toUpperCase() + word.slice(1)
        words[parseInt(ix) + 1] = newWord
    }
    return words.join("")
}

const getCsrfCookie = () => {
    let cookie: string
    if (process.server) {
        cookie = useRequestHeaders(["cookie"])["cookie"]!
    } else {
        cookie = document.cookie
    }
    if (!cookie) {
        return null
    }
    const csrfRow = cookie.split("; ").find((row) => row.startsWith("csrftoken="))
    if (!csrfRow) {
        return null
    }
    return csrfRow.split("=")[1]
}

const getHeaders = (includeCsrf = false): MyHeaders => {
    const headers: MyHeaders = useRequestHeaders(["cookie"])
    if (includeCsrf) {
        const csrfToken = getCsrfCookie()
        if (csrfToken) {
            headers["X-CSRFTOKEN"] = csrfToken
        }
    }
    return headers
}

export const BASE_API_URL = base_url

export async function useApiRequest<Type>(
    method: string,
    path: string,
    payload: any,
    params = {},
    onSuccess: Alert | string | null = null,
    // if onError is true, the alert title and message is built from API response
    onError: Alert | string | boolean = false,
    spinnerMessage: boolean | string = false,
    customKey = ""
) {
    const loadingStore = useLoadingStore()
    const alertStore = useAlertStore()

    let key = customKey
    if (key === "") {
        key = makeLoadingKey(path)
    }
    loadingStore.markLoading(key, spinnerMessage)
    const { data, error, pending } = await useAsyncData<Type>(
        key,
        () =>
            $fetch(BASE_API_URL + "/api/" + path, {
                method: method,
                body: payload,
                credentials: "include",
                headers: getHeaders(method != "GET"),
                params: params,
            }),
        { initialCache: false }
    )

    // handle alerts and loading status
    if (error.value) {
        loadingStore.markError(key)
        if (onError === true) {
            alertStore.alert(
                "Erreur lors de la requête",
                `${error.value.message} : ${JSON.stringify(error.value.data)}`,
                "error"
            )
        } else if (onError) {
            let title: string
            let text: string | object = ""
            let type = "error"
            if (typeof onError === "string") {
                title = onError
            } else {
                title = onError.title
                text = onError.text || ""
                type = onError.type || type
                if (text === "_responseBody") {
                    text = error.value.data
                    if (typeof text == "string") {
                    } else if (Array.isArray(text)) {
                        text = text.join(". ")
                    } else {
                        text = JSON.stringify(text)
                    }
                }
            }
            alertStore.alert(title, text, type)
        }
    } else {
        loadingStore.markDone(key)
        if (onSuccess) {
            let title: string
            let text = ""
            let type = "success"
            if (typeof onSuccess === "string") {
                title = onSuccess
            } else {
                title = onSuccess.title
                text = onSuccess.text || ""
                type = onSuccess.type || type
            }
            alertStore.alert(title, text, type)
        }
    }
    return { data, error, pending }
}

export async function useApiGet<Type>(
    path: string,
    params = {},
    onSuccess: Alert | string | null = null,
    onError: Alert | string | boolean = false,
    spinnerMessage: boolean | string = false,
    customKey = ""
) {
    return useApiRequest<Type>(
        "GET",
        path,
        undefined,
        params,
        onSuccess,
        onError,
        spinnerMessage,
        customKey
    )
}

export async function useApiPost<Type>(
    path: string,
    payload = {},
    params = {},
    onSuccess: Alert | string | null = null,
    onError: Alert | string | boolean = false,
    spinnerMessage: boolean | string = false,
    customKey = ""
) {
    return useApiRequest<Type>(
        "POST",
        path,
        payload,
        params,
        onSuccess,
        onError,
        spinnerMessage,
        customKey
    )
}

export async function useApiPatch<Type>(
    path: string,
    payload = {},
    params = {},
    onSuccess: Alert | string | null = null,
    onError: Alert | string | boolean = false,
    spinnerMessage: boolean | string = false,
    customKey = ""
) {
    return useApiRequest<Type>(
        "PATCH",
        path,
        payload,
        params,
        onSuccess,
        onError,
        spinnerMessage,
        customKey
    )
}

export async function useApiDelete<Type>(
    path: string,
    params = {},
    onSuccess: Alert | string | null = null,
    onError: Alert | string | boolean = false,
    spinnerMessage: boolean | string = false,
    customKey = ""
) {
    return useApiRequest<Type>(
        "DELETE",
        path,
        undefined,
        params,
        onSuccess,
        onError,
        spinnerMessage,
        customKey
    )
}
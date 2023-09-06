<template>
    <form @submit.prevent="">
        <div class="field">
            <label class="label">Nom du document</label>
            <div class="control">
                <input v-model="name" class="input" type="text" placeholder="Mon nom de fichier">
            </div>
        </div>
        <div class="field">
            <label class="label">Fichier</label>
            <div class="control">
                <div class="file has-name is-boxed">
                    <label class="file-label">
                        <input class="file-input" type="file" name="resume" @change="handleFile">
                        <span class="file-cta">
                            <span class="file-icon">
                                <icon name="file-upload-line" />
                            </span>
                            <span class="file-label is-size-7">
                                Choisissez un fichier...
                            </span>
                        </span>
                        <span v-if="selectedFileName" class="file-name">
                            {{ selectedFileName }}
                        </span>
                    </label>
                </div>
            </div>
        </div>
        <button class="button is-rounded is-dark" :disabled="loadingStore.isLoading('documents')" @click="saveEdits">
            <span>Valider</span>
            <span class="icon">
                <icon size="16" name="check" />
            </span>
        </button>
    </form>
</template>

<script setup lang="ts">
const name = ref("")
const selectedFileParams = ref<any>({})
const selectedFileName = ref<string>("")


export const getBase64 = (file: File) => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.readAsDataURL(file)
        reader.onload = () => resolve(reader.result)
        reader.onerror = error => reject(error)
    })
}
const handleFile = async (event) => {
    const file = event.target.files[0]
    selectedFileParams.value = { base64: await getBase64(file) as string, name: file.name }
    selectedFileName.value = file.name
}
const saveEdits = async () => {
    const data = {
        file: selectedFileParams.value,
        name: name.value
    }
    await uploadDocument(data, props.assessmentId)
}
// probably more in a store
const uploadDocument = (data) => {
    const { data, error } = await useApiPost<DocumentType>(
        `documents/`,
        data,
        "Impossible de téléverser le document"
    )
    if (!error.value) {
        notifyUser("Téléversement effectué")
    }

}
</script>


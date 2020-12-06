<template>
  <v-card>

    <girder-upload
      :dest="{ batchId, fieldId: 'core.Image.blob' }"
      :upload-cls="FileUploadHandler"
      @done="uploadDone"
      :max-show="5"
    >
      <template #header><div></div></template>
    </girder-upload>
    <div class="title px-3 mt-3">
      Pending files
      <span v-if="!loading">({{ count }})</span>
    </div>
    <v-data-table
      :loading="loading"
      item-key="id"
      :items="pendingUploads"
      :headers="headers"
    >
    </v-data-table>
  </v-card>
</template>

<script>
import GirderUpload from '@girder/components/src/components/Upload.vue';
import { FileUploadHandler } from '../upload';

export default {
  components: {
    GirderUpload,
  },
  inject: ['girderRest'],
  props: {
    batchId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      pendingUploads: [],
      count: 0,
      // TODO should we show the metadata fields in the table?
      headers: [
        {
          text: 'Name',
          value: 'name',
        },
        {
          text: 'Patient identifier',
          value: 'patient',
        },
      ],
    };
  },
  async created() {
    this.FileUploadHandler = FileUploadHandler;
  },
  async mounted() {
    // TODO pagination
    this.loading = true;
    const resp = await this.girderRest.get('pending_uploads', { params: {
      batch: this.batchId,
      limit: 500,
    }});
    this.pendingUploads = resp.data.results;
    this.count = resp.data.count;
    this.loading = false;
  },
};
</script>

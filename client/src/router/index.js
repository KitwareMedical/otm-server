import Vue from 'vue';
import VueRouter from 'vue-router';
import {
  CreateUploadBatch,
  Dataset,
  Datasets,
  DatasetImages,
  PendingUploads,
  UploadBatch,
} from '../views';

Vue.use(VueRouter);

const routes = [
  {
    path: '/',
    redirect: '/datasets',
  },
  {
    path: '/datasets',
    component: Datasets,
  },
  {
    path: '/dataset/:datasetId',
    component: Dataset,
    props: true,
    children: [
      {
        path: 'images',
        component: DatasetImages,
        props: true,
      },
      {
        path: 'upload',
        component: CreateUploadBatch,
        props: true,
      },
      {
        path: 'uploads',
        component: PendingUploads,
        props: true,
      }
    ],
  },
  {
    path: '/upload/:batchId',
    component: UploadBatch,
    props: true,
  },
];

const router = new VueRouter({
  routes,
});

export default router;

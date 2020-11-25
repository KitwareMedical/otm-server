import Vue from 'vue';
import VueRouter from 'vue-router';
import { CreateUploadBatch, Datasets, UploadBatch } from '../views';

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
    path: '/upload/:datasetId',
    component: CreateUploadBatch,
    props: true,
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

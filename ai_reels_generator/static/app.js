import { getElements } from "./js/dom.js";
import { bindUploadFlow } from "./js/upload.js";


const elements = getElements();
const state = {
  activeJobIds: [],
};

bindUploadFlow(elements, state);

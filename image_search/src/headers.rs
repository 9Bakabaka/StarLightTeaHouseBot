use pyo3::prelude::*;

pub struct Result {
    pub similarity: f32,
    pub thumbnail_url: String,
    pub external_url: Vec<String>,
    pub source: String,
}

impl Result {
    //constrrrrrrrructor
    pub fn new(similarity: f32, thumbnail_url: String, external_url: Vec<String>, source: String) -> Self {
        Self {
            similarity,
            thumbnail_url,
            external_url,
            source,
        }
    }

    // for test
    pub fn display(&self) -> String {
        let urls = self.external_url.join(", ");
        /*return*/ format!(
            "Similarity: {:.2}%, source: {}, external url: {}, thumbnail: {}",
            self.similarity, self.source, urls, self.thumbnail_url
        )
    }

    // convert to python dict
    pub fn as_py_dict(&self, py: Python) -> PyObject {
        use pyo3::types::{PyDict, PyList};
        let dict = PyDict::new(py);
        dict.set_item("similarity", self.similarity).unwrap();
        dict.set_item("thumbnail_url", &self.thumbnail_url).unwrap();
        dict.set_item("external_url", PyList::new(py, &self.external_url)).unwrap();
        dict.set_item("source", &self.source).unwrap();
        /*return*/ dict.into()
    }
}
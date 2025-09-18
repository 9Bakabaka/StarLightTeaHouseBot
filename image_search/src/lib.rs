mod headers;
mod saucenao;
use pyo3::prelude::*;

#[pyfunction]
fn saucenao_search(py: Python, api_key: &str, image_path: String) -> PyResult<Vec<PyObject>> {
    let rt = tokio::runtime::Runtime::new()?;
    let results = rt.block_on(saucenao::search(api_key, &image_path));
    // Convert Rust/Vec<Result> to Python/List[Dict, ...]
    match results {
        Ok(res_vec) => {
            let dicts = res_vec.into_iter()
                // convert each Result to Python dict
                .map(|r| r.as_py_dict(py))
                .collect();
            Ok(dicts)
        },
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
    }
}

#[pymodule]
fn image_search(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(saucenao_search, m)?)?;
    Ok(())
}
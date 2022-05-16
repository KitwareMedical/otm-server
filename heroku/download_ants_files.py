import site
import tempfile
import urllib.request
import zipfile

wheel_url = (
    'https://files.pythonhosted.org/packages/f0/b5'
    '/45f1d9ad34194bf4b9cc79c7b30b2d8c656ab6b487d8c70c8826f6a9f922'
    '/antspyx-0.3.2-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'
)


def main():
    dest_dir = site.getsitepackages()[0]
    with tempfile.NamedTemporaryFile() as tmp:
        wheel_file = tmp.name

        print('Downloading python wheel...')
        urllib.request.urlretrieve(wheel_url, wheel_file)

        print('Extracting files...')
        with zipfile.ZipFile(wheel_file, 'r') as zip_ref:
            lib_files = [f for f in zip_ref.namelist() if f.startswith('ants/lib/')]
            zip_ref.extractall(dest_dir, members=lib_files)

        print('...Done')


if __name__ == '__main__':
    main()

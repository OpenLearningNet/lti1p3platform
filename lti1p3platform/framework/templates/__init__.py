import pkg_resources

from jinja2 import Environment, PackageLoader

# Create a Jinja2 environment and specify the template folder
env = Environment(
    loader=PackageLoader(
        "lti1p3platform.framework",
        package_path="templates",
    )
)

# Load a template named 'launch.html'
template = env.get_template("launch.html")

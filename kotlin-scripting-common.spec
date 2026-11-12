Name:		kotlin-scripting-common
Version:	2.4.21
Release:	1
Summary:	Kotlin scripting common library
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/JetBrains/kotlin
# Kotlin tag v2.4.21, libraries/scripting/common.
# kotlinc 2.0.21 rejects name-based destructuring. Patch0 rewrites five
# lambdas from [a, b] to (a, b). Each value is a Pair or a Map.Entry.
Patch0:		kotlin-scripting-common-destructure.patch
Source0:	kotlin-scripting-common-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	kotlin
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-reflect)

%description
org.jetbrains.kotlin:kotlin-scripting-common %{version}.
Script diagnostic and compilation-configuration types from Kotlin v2.4.21,
compiled with the installed kotlinc 2.0.21.

%prep
%autosetup -n kotlin-scripting-common-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
CPSTD=%{_javadir}/kotlin-stdlib.jar
CPREF=%{_javadir}/kotlin-reflect.jar
test -s "$CPSTD"
test -s "$CPREF"
mkdir -p classes
find src -name '*.kt' > sources.list
test "$(wc -l < sources.list)" -eq 21
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 \
	-Xallow-kotlin-package -no-stdlib \
	-opt-in=kotlin.ExperimentalStdlibApi \
	-cp "$CPSTD:$CPREF" -d classes @sources.list
test -s classes/kotlin/script/experimental/api/ScriptDiagnostic.class
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: kotlin.scripting.common' > manifest.mf
jar cfm kotlin-scripting-common.jar manifest.mf -C classes .
jar i kotlin-scripting-common.jar
desc=$(jar --describe-module --file kotlin-scripting-common.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -qx 'kotlin.scripting.common automatic'
cat > kotlin-scripting-common.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jetbrains.kotlin</groupId>
  <artifactId>kotlin-scripting-common</artifactId>
  <version>%{version}</version>
  <name>kotlin-scripting-common</name>
  <description>Kotlin scripting common library</description>
  <url>https://github.com/JetBrains/kotlin</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-stdlib</artifactId>
      <version>2.0.21</version>
    </dependency>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-reflect</artifactId>
      <version>2.0.21</version>
    </dependency>
  </dependencies>
</project>
END


%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact kotlin-scripting-common.pom:kotlin-scripting-common.jar \
	--file-name kotlin-scripting-common \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.jetbrains.kotlin/kotlin-scripting-common.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "kotlin-scripting-common"' "$idx"
test -s %{buildroot}%{_javadir}/kotlin-scripting-common.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
JAR=%{buildroot}%{_javadir}/kotlin-scripting-common.jar
test -s "$JAR"
STDLIB=%{_javadir}/kotlin-stdlib.jar
REFLECT=%{_javadir}/kotlin-reflect.jar
mkdir -p check
cat > check/ScriptDiag.kt << 'EOF'
import kotlin.script.experimental.api.ScriptDiagnostic
import kotlin.script.experimental.api.isError

fun main() {
    val diagnostic = ScriptDiagnostic(ScriptDiagnostic.unspecifiedError, "gradle")
    if (!diagnostic.isError()) error("expected error severity")
    if (diagnostic.message != "gradle") error("message")
    println("kotlin_scripting_common_ok " + diagnostic.message)
}
EOF
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 \
	-cp "$JAR:$STDLIB:$REFLECT" -d check/out check/ScriptDiag.kt
java -cp "check/out:$JAR:$STDLIB:$REFLECT" ScriptDiagKt > check/out.txt
cat check/out.txt
grep -F -qx 'kotlin_scripting_common_ok gradle' check/out.txt

%files -f .mfiles
%license LICENSE.txt
%doc NOTICE.txt

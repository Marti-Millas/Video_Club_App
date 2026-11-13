import os
import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography import x509

def generate_cert(name, ca_key=None, ca_cert=None, is_ca=False):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    if not is_ca:
        issuer = ca_cert.subject

    cert_builder = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    )

    # Identificadors de clau (el que vam arreglar abans)
    ski = x509.SubjectKeyIdentifier.from_public_key(private_key.public_key())
    cert_builder = cert_builder.add_extension(ski, critical=False)

    issuer_key = ca_key.public_key() if ca_key else private_key.public_key()
    aki = x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key)
    cert_builder = cert_builder.add_extension(aki, critical=False)

    if is_ca:
        # Extensions específiques per a la CA
        cert_builder = cert_builder.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        cert_builder = cert_builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True, # Això és el que demana el teu error!
                crl_sign=True,
                encipher_only=False,
                decipher_only=False
            ), critical=True
        )
    else:
        # Extensions específiques per a clients i servidor
        cert_builder = cert_builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            ), critical=True
        )
        
    signer_key = ca_key if ca_key else private_key
    cert = cert_builder.sign(signer_key, hashes.SHA256())

    os.makedirs("certs", exist_ok=True)
    with open(f"certs/{name}_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(f"certs/{name}_cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        
    return private_key, cert

if __name__ == "__main__":
    print("Generant CA i certificats amb totes les extensions (KeyUsage inclòs)...")
    ca_key, ca_cert = generate_cert("CA", is_ca=True)
    generate_cert("server", ca_key, ca_cert)
    generate_cert("client1", ca_key, ca_cert)
    generate_cert("client2", ca_key, ca_cert)
    print("Tots els certificats s'han regenerat a la carpeta /certs!")